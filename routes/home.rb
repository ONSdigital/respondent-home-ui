require 'sinatra'
require 'sinatra/content_for2'
require 'sinatra/flash'
require 'sinatra/formkeeper'
require 'iac-validator'
require 'rest_client'
require 'ons-jwe'
require 'openssl'
require 'json'
require 'yaml'

KEY_ID                    = 'EDCRRM'.freeze
SESSION_EXPIRATION_PERIOD = 60 * 60 * 6

# Load various settings from a configuration file.
config = YAML.load_file(File.join(__dir__, '../config.yml'))
set :locale,                 ENV['RESPONDENT_HOME_LOCALE']
set :eq_service_host,        ENV['RESPONDENT_HOME_EQ_HOST']
set :eq_service_port,        ENV['RESPONDENT_HOME_EQ_PORT']
set :iac_service_host,       ENV['RESPONDENT_HOME_IAC_SERVICE_HOST']
set :iac_service_port,       ENV['RESPONDENT_HOME_IAC_SERVICE_PORT']
set :public_key,             config['eq-service']['public_key']
set :private_key,            config['eq-service']['private_key']
set :private_key_passphrase, config['eq-service']['private_key_passphrase']

# Display badges with the built date, environment and commit SHA in
# non-production environments.
set :built, config['badges']['built']
set :commit, config['badges']['commit']
set :environment, config['badges']['environment']

# Configure internationalisation.
I18n.load_path = Dir['locale/*.yml']
I18n.backend.load_translations
I18n.default_locale = settings.locale
I18n.locale = settings.locale

# Expire sessions after SESSION_EXPIRATION_PERIOD minutes of inactivity.
use Rack::Session::Cookie, key: 'rack.session', path: '/',
                           secret: 'f089802942494ca9a7250a849d8d8c0c',
                           expire_after: SESSION_EXPIRATION_PERIOD

# View helper for defining blocks inside views for rendering in templates.
helpers Sinatra::ContentFor2
helpers do
  # Returns the IAC lowercased and with any spaces removed.
  def canonicalize_iac(iac)
    iac.downcase.tr(' ', '')
  end

  def claims(iac)
    {
      user_id: iac,
      iat: Time.now.to_i,
      exp: Time.now.to_i + 60 * 60,
      eq_id: '1',
      period_str: '2016-01-01',
      period_id: '2016-01-01',
      form_type: '0205',
      collection_exercise_sid: '789',
      ref_p_start_date: '2016-01-01',
      ref_p_end_date: '2016-09-01',
      ru_ref: '12346789012A',
      ru_name: 'Office for National Statistics',
      return_by: '2016-04-30',
      employment_date: '2016-06-10'
    }
  end

  # View helper for escaping HTML output.
  def h(text)
    Rack::Utils.escape_html(text)
  end

  def load_key_from_file(file, passphrase = nil)
    OpenSSL::PKey::RSA.new(File.read(File.join(__dir__, file)), passphrase)
  end
end

before do
  headers 'Content-Type' => 'text/html; charset=utf-8'
  @built  = settings.built
  @commit = settings.commit

  # Display the correct built date and commit SHA when running locally.
  @built = Date.today.strftime('%d_%b_%Y') if @built == '01_Jan_1970'
  @commit = `git rev-parse --short HEAD` if @commit == 'commit'
end

get '/' do
  erb :index, locals: { title: I18n.t('welcome'),
                        built: @built,
                        commit: @commit,
                        environment: settings.environment }
end

post '/' do
  form do
    field :iac, present: true
  end

  if form.failed?
    flash[:notice] = I18n.t('iac_required')
    redirect '/'
  else
    iac = canonicalize_iac(params[:iac])

    unless InternetAccessCodeValidator.new(iac).valid?
      flash[:notice] = I18n.t('iac_invalid')
      redirect '/'
    end

    iac_response = []
    RestClient.get("http://#{settings.iac_service_host}:#{settings.iac_service_port}/iacs/#{iac}") do |response, _request, _result, &_block|
      iac_response = JSON.parse(response)
      redirect_url = '/'

      if response.code == 404
        flash[:notice] = I18n.t('iac_invalid')
      elsif iac_response['active'] == false
        flash[:notice] = I18n.t('iac_used')
      else
        public_key  = load_key_from_file(settings.public_key)
        private_key = load_key_from_file(settings.private_key,
                                         settings.private_key_passphrase)

        token        = JWEToken.new(KEY_ID, claims(iac), public_key, private_key)
        redirect_url = "http://#{settings.eq_service_host}:#{settings.eq_service_port}/session?token=#{token.value}"
      end

      redirect redirect_url
    end
  end
end
