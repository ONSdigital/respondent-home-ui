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

require_relative '../lib/configuration'
require_relative '../lib/claims'

KEY_ID                    = 'EDCRRM'.freeze
SESSION_EXPIRATION_PERIOD = 60 * 60 * 6

config = Configuration.new(ENV)
set :analytics_account,            config.analytics_account
set :eq_host,                      config.eq_host
set :eq_port,                      config.eq_port
set :iac_service_host,             config.iac_service_host
set :iac_service_port,             config.iac_service_port
set :locale,                       config.locale

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
                        host: settings.host,
                        built: @built,
                        commit: @commit,
                        environment: settings.environment,
                        analytics_account: settings.analytics_account,
                        locale: settings.locale }
end

post '/' do
  form do
    field :iac1, present: true
    field :iac2, present: true
    field :iac3, present: true
  end

  if form.failed?
    flash[:notice] = I18n.t('iac_required')
    redirect '/'
  else
    iac = canonicalize_iac(form[:iac1], form[:iac2], form[:iac3])

    unless InternetAccessCodeValidator.new(iac).valid?
      flash[:notice] = I18n.t('iac_invalid')
      redirect '/'
    end

    case_summary = []
    RestClient.get("http://#{settings.iac_service_host}:#{settings.iac_service_port}/iacs/#{iac}") do |response, _request, _result, &_block|
      case_summary = JSON.parse(response)
      url = '/'

      if response.code == 404
        flash[:notice] = I18n.t('iac_invalid')
      elsif case_summary['active'] == false
        flash[:notice] = I18n.t('iac_used')
      else
        public_key  = load_key_from_file(settings.public_key)
        private_key = load_key_from_file(settings.private_key,
                                         settings.private_key_passphrase)

        claims = Claims.new(case_summary['caseId'], case_summary['questionSet'], settings.locale)
        token  = JWEToken.new(KEY_ID, claims.to_hash, public_key, private_key)
        url    = "#{settings.eq_protocol}://#{settings.eq_host}:#{settings.eq_port}/session?token=#{token.value}"
      end

      redirect url
    end
  end
end
