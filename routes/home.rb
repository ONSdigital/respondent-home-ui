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
set :iac_service_host,       config['iac-webservice']['host']
set :iac_service_port,       config['iac-webservice']['port']
set :eq_service_host,        config['eq-service']['host']
set :eq_service_port,        config['eq-service']['port']
set :public_key,             config['eq-service']['public_key']
set :private_key,            config['eq-service']['private_key']
set :private_key_passphrase, config['eq-service']['private_key_passphrase']

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

# Always send UTF-8 Content-Type HTTP header.
before do
  headers 'Content-Type' => 'text/html; charset=utf-8'
end

get '/' do
  erb :index, locals: { title: 'Welcome' }
end

post '/' do
  form do
    field :iac, present: true
  end

  if form.failed?
    flash[:notice] = 'An Internet access code is required.'
    redirect '/'
  else
    iac = canonicalize_iac(params[:iac])

    unless InternetAccessCodeValidator.new(iac).valid?
      flash[:notice] = 'The Internet access code entered is not valid.'
      redirect '/'
    end

    iac_response = []
    RestClient.get("http://#{settings.iac_service_host}:#{settings.iac_service_port}/iacs/#{iac}") do |response, _request, _result, &_block|
      iac_response = JSON.parse(response)
      redirect_url = '/'
      
      if response.code == 404
        flash[:notice] = 'The Internet access code entered is not valid.'
      elsif iac_response['active'] == false
        flash[:notice] = 'The Internet access code entered has already been used.'
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

get '/help' do
  erb :help, locals: { title: 'Help' }
end
