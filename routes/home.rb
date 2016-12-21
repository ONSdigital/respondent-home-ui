require 'sinatra'
require 'http/accept/languages'
require 'sinatra/content_for2'
require 'sinatra/formkeeper'
require 'sinatra/flash'
require 'user_agent_parser'
require 'iac-validator'
require 'rest_client'
require 'ons-jwe'
require 'openssl'
require 'json'
require 'yaml'

require_relative '../lib/configuration'
require_relative '../lib/email_job'
require_relative '../lib/claims'

KEY_ID                    = 'EDCRRM'.freeze
SESSION_EXPIRATION_PERIOD = 60 * 30

# Load configuration from environment variables and configuration file.
config = Configuration.new(ENV)
set :analytics_account,            config.analytics_account
set :eq_host,                      config.eq_host
set :eq_port,                      config.eq_port
set :eq_protocol,                  config.eq_protocol
set :iac_service_host,             config.iac_service_host
set :iac_service_port,             config.iac_service_port
set :iac_service_protocol,         config.iac_service_protocol
set :iac_service_user,             config.iac_service_user
set :iac_service_password,         config.iac_service_password
set :notify_api_key,               config.notify_api_key
set :notify_email_address,         config.notify_email_address
set :notify_template_id,           config.notify_template_id

config_file = YAML.load_file(File.join(__dir__, '../config.yml'))
set :public_key,             config_file['eq-service']['public_key']
set :private_key,            config_file['eq-service']['private_key']
set :private_key_passphrase, config_file['eq-service']['private_key_passphrase']

# Configure logging.
SuckerPunch.logger = Logger.new($stdout)

# Configure internationalisation.
I18n.load_path = Dir['locale/*.yml']
I18n.backend.load_translations

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

  # View helper for escaping HTML output.
  def h(text)
    Rack::Utils.escape_html(text)
  end

  def load_key_from_file(file, passphrase = nil)
    OpenSSL::PKey::RSA.new(File.read(File.join(__dir__, file)), passphrase)
  end

  def locale_from_request
    languages = HTTP::Accept::Languages.parse(request.env['HTTP_ACCEPT_LANGUAGE'])
    return 'cy' if languages.first.locale.include?('cy')
    request.url.include?('cyfrifiad') ? 'cy' : 'en'
  end

  def parse_user_agent
    UserAgentParser.parse(request.env['HTTP_USER_AGENT'])
  end
end

before do
  headers 'Content-Type' => 'text/html; charset=utf-8'

  # Need to get the correct client IP address when behind a load balancer.
  @client_ip = request.env['HTTP_X_FORWARDED_FOR'] || request.ip
  @locale    = locale_from_request
  I18n.default_locale = @locale
  I18n.locale         = @locale
end

get '/' do
  erb :home, locals: { title: I18n.t('home_heading1'),
                       locale: @locale,
                       analytics_account: settings.analytics_account }
end

post '/' do
  form do
    field :iac1, present: true, regexp: /^[a-zA-Z0-9]{4}$/
    field :iac2, present: true, regexp: /^[a-zA-Z0-9]{4}$/
    field :iac3, present: true, regexp: /^[a-zA-Z0-9]{4}$/
  end

  if form.failed?
    flash[:notice] = I18n.t('home_iac_invalid')
    redirect '/'
  else
    iac = canonicalize_iac(form[:iac1], form[:iac2], form[:iac3])

    unless InternetAccessCodeValidator.new(iac).valid?
      flash[:notice] = I18n.t('home_iac_invalid')
      redirect '/'
    end

    case_summary = []

    # See https://www.krautcomputing.com/blog/2015/06/21/how-to-use-basic-authentication-with-the-ruby-rest-client-gem/
    RestClient::Request.execute(method: :get,
                                url: "#{settings.iac_service_protocol}://#{settings.iac_service_host}:#{settings.iac_service_port}/iacs/#{iac}",
                                user: settings.iac_service_user,
                                password: settings.iac_service_password) do |response, _request, _result, &_block|
      case_summary = JSON.parse(response)
      url = '/'

      if response.code == 404
        flash[:notice] = I18n.t('home_iac_invalid')

      # The IAC has no associated case.
      elsif response.code == 500 &&
            case_summary['error']['message'].include?('Case not found')
        flash[:notice] = I18n.t('home_iac_invalid')
      elsif case_summary['active'] == false
        flash[:notice] = I18n.t('home_iac_used')
      else
        public_key  = load_key_from_file(settings.public_key)
        private_key = load_key_from_file(settings.private_key,
                                         settings.private_key_passphrase)

        claims = Claims.new(case_summary['caseRef'], case_summary['questionSet'], @locale)
        logger.info "Redirecting #{@client_ip} to eQ, tx_id='#{claims.transaction_id}'"
        token  = JWEToken.new(KEY_ID, claims.to_hash, public_key, private_key)
        url    = "#{settings.eq_protocol}://#{settings.eq_host}:#{settings.eq_port}/session?token=#{token.value}"
      end

      redirect url
    end
  end
end
