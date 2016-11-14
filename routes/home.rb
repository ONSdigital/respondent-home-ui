require 'sinatra'
require 'sinatra/content_for2'
require 'sinatra/flash'
require 'sinatra/formkeeper'
require 'iac-validator'
require 'securerandom'
require 'rest_client'
require 'ons-jwe'
require 'openssl'
require 'json'
require 'yaml'

require_relative '../lib/authentication_policy'
require_relative '../lib/configuration'

KEY_ID                    = 'EDCRRM'.freeze
SESSION_EXPIRATION_PERIOD = 60 * 60 * 6

config = Configuration.new(ENV)
set :locale,                       config.locale
set :eq_host,                      config.eq_host
set :eq_port,                      config.eq_port
set :iac_service_host,             config.iac_service_host
set :iac_service_port,             config.iac_service_port
set :iac_attempts_expiration_secs, config.iac_attempts_expiration_secs
set :max_iac_attempts,             config.max_iac_attempts
set :redis_host,                   config.redis_host
set :redis_port,                   config.redis_port
set :redis_password,               config.redis_password

config_file = YAML.load_file(File.join(__dir__, '../config.yml'))
set :public_key,             config_file['eq-service']['public_key']
set :private_key,            config_file['eq-service']['private_key']
set :private_key_passphrase, config_file['eq-service']['private_key_passphrase']

# Display badges with the host, built date, commit SHA and environment in
# non-production environments.
set :host,        `hostname`.strip.gsub(/-/, '--')
set :built,       config_file['badges']['built']
set :commit,      config_file['badges']['commit']
set :environment, config_file['badges']['environment']

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
  # Returns the IAC from its segments and lowercased.
  def canonicalize_iac(*segments)
    segments.join.downcase
  end

  # Returns the eQ claims for the passed case reference and question set.
  def claims_for(case_ref, question_set)
    {
      collection_exercise_sid: '2017',
      eq_id: '1',
      exp: Time.now.to_i + 60 * 60,
      form_type: question_set,
      iat: Time.now.to_i,
      period_id: '1',
      period_str: '2016-01-01',
      ref_p_start_date: '2016-01-01',
      ref_p_end_date: '2016-09-01',
      region_code: settings.locale == 'cy' ? 'GB-WLS' : 'GB-ENG',
      ru_name: 'Office for National Statistics',
      ru_ref: '12346789012A',
      return_by: '2016-04-30',
      tx_id: SecureRandom.uuid,
      user_id: case_ref
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
  @authentication_policy ||= AuthenticationPolicy.new(settings, request.ip)
  @built  = settings.built
  @commit = settings.commit

  # Display the correct built date and commit SHA when running locally.
  @built = Date.today.strftime('%d_%b_%Y') if @built == '01_Jan_1970'
  @commit = `git rev-parse --short HEAD` if @commit == 'commit'
end

get '/' do
  halt 429 if @authentication_policy.client_blocked?
  
  erb :index, locals: { title: I18n.t('welcome'),
                        host: settings.host,
                        built: @built,
                        commit: @commit,
                        environment: settings.environment,
                        locale: settings.locale }
end

post '/' do
  halt 429 if @authentication_policy.client_blocked?

  form do
    field :iac1, present: true
    field :iac2, present: true
    field :iac3, present: true
  end

  if form.failed?
    @authentication_policy.failed_attempt!
    flash[:notice] = I18n.t('iac_required')
    redirect '/'
  else
    iac = canonicalize_iac(form[:iac1], form[:iac2], form[:iac3])

    unless InternetAccessCodeValidator.new(iac).valid?
      @authentication_policy.failed_attempt!
      flash[:notice] = I18n.t('iac_invalid')
      redirect '/'
    end

    case_summary = []
    RestClient.get("http://#{settings.iac_service_host}:#{settings.iac_service_port}/iacs/#{iac}") do |response, _request, _result, &_block|
      case_summary = JSON.parse(response)
      redirect_url = '/'

      if response.code == 404
        flash[:notice] = I18n.t('iac_invalid')
      elsif case_summary['active'] == false
        flash[:notice] = I18n.t('iac_used')
      else
        public_key  = load_key_from_file(settings.public_key)
        private_key = load_key_from_file(settings.private_key,
                                         settings.private_key_passphrase)

        claims       = claims_for(case_summary['caseRef'], case_summary['questionSet'])
        token        = JWEToken.new(KEY_ID, claims, public_key, private_key)
        redirect_url = "http://#{settings.eq_host}:#{settings.eq_port}/session?token=#{token.value}"
      end

      redirect redirect_url
    end
  end
end
