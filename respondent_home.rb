require 'sinatra'
require 'sinatra/content_for2'
require 'sinatra/flash'
require 'sinatra/formkeeper'
require 'rest_client'
require 'json'
require 'yaml'
require 'jwt'

SESSION_EXPIRATION_PERIOD = 60 * 60 * 6

# Expire sessions after ten minutes of inactivity.
use Rack::Session::Cookie, key: 'rack.session', path: '/',
                           secret: 'eb46fa947d8411e5996329c9ef0ba35d',
                           expire_after: SESSION_EXPIRATION_PERIOD

# Load various settings from a configuration file.
config = YAML.load_file(File.join(__dir__, '/config/config.yml'))
set :frame_service_host, config['frame-webservice']['host']
set :frame_service_port, config['frame-webservice']['port']
set :eq_service_host, config['eq-service']['host']
set :eq_service_port, config['eq-service']['port']

# Set global view options.
set :erb, escape_html: false

# View helper for defining blocks inside views for rendering in templates.
helpers Sinatra::ContentFor2
helpers do
  # View helper for escaping HTML output.
  def h(text)
    Rack::Utils.escape_html(text)
  end
end

# Always send UTF-8 Content-Type HTTP header.
before do
  headers 'Content-Type' => 'text/html; charset=utf-8'
end

error 404 do
  erb :not_found, locals: { title: '404 Not Found' }
end

error 500 do
  erb :internal_server_error, locals: { title: '500 Internal Server Error' }
end

# Home page.
get '/' do
  erb :index, layout: :simple_layout, locals: { title: 'Home' }
end

# Home Page.
post '/' do

  # test for existence of iac
  form do
    field :iac, present: true
  end

  if form.failed?
    flash[:notice] = 'Internet access code required.'
    redirect '/'
  else
    iac = params[:iac]
    iac_response = []
    RestClient.get("http://#{settings.frame_service_host}:#{settings.frame_service_port}/questionnaires/iac/#{iac}") do |response, _request, _result, &_block|
      iac_response = JSON.parse(response)
      if response.code == 404
        flash[:notice] = 'Invalid Internet Access Code.'
        redirect '/'
      elsif iac_response['responseDateTime']
        flash[:notice] = 'Questionnaire has been completed.'
        redirect '/'
      else

        iat = Time.now.to_i
        exp = Time.now.to_i + (60 * 60)

        logger.info iat
        logger.info exp
        payload = {  user_id: iac_response['iac'],
                     ru_ref: '789789789c',
                     ru_name: 'APPLE',
                     eq_id: '10',
                     collection_exercise_sid: '789',
                     period_id: '201605',
                     period_str: 'May 2016',
                     ref_p_start_date: '2016-07-01',
                     ref_p_end_date: '2016-07-31',
                     employment_date: '2016-06-10',
                     trad_as: 'Apple',
                     form_type: '2011',
                     return_by: '2016-07-30',
                     iat: iat,
                     exp: exp
                  }

        # IMPORTANT: set nil as password parameter
        token = JWT.encode payload, nil, 'none'

        logger.info token
        url = "http://#{settings.eq_service_host}:#{settings.eq_service_port}/session?token=#{token}"
        redirect url
      end
    end
  end
end

get '/help' do
  erb :help, layout: :simple_layout, locals: { title: 'Help' }
end
