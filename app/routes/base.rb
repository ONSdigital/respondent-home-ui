require 'sinatra/content_for2'
require 'sinatra/flash'
require 'sinatra/formkeeper'
require 'will_paginate'
require 'will_paginate/array'
require 'rest_client'
require 'json'
require 'yaml'
require 'jwt'


module Beyond
  module Routes

    class Base < Sinatra::Application
      configure do

        # Load various settings from a configuration file.
        config = YAML.load_file(File.join(__dir__, '../../config/config.yml'))
        set :frame_service_host, config['frame-webservice']['host']
        set :frame_service_port, config['frame-webservice']['port']
        set :eq_service_host, config['eq-service']['host']


        # Display badges with the built date, environment and commit SHA on the
        # Sign In screen in non-production environments.
        set :built, config['badges']['built']
        set :commit, config['badges']['commit']
        set :environment, config['badges']['environment']


        # Set global view options.
        set :erb, escape_html: false
        set :views, File.dirname(__FILE__) + '/../views'
        set :public_folder, File.dirname(__FILE__) + '/../../public'

        # Set global pagination options.
        WillPaginate.per_page = 20
      end

      # View helper for defining blocks inside views for rendering in templates.
            helpers Sinatra::ContentFor2
            helpers do

              # Follow-up helpers.
              def active(follow_up)
                follow_up['status'].downcase == 'active'
              end

              def cancelling(follow_up)
                follow_up['status'].downcase == 'cancelling'
              end

              # View helper for escaping HTML output.
              def h(text)
                Rack::Utils.escape_html(text)
              end
            end

      # Always send UTF-8 Content-Type HTTP header.
      before do
        headers 'Content-Type' => 'text/html; charset=utf-8'
      end

      # Error pages.
      error 403 do
        erb :forbidden, locals: { title: '403 Forbidden' }
      end

      error 404 do
        erb :not_found, locals: { title: '404 Not Found' }
      end

      # error 500 do
      #   erb :internal_server_error, locals: { title: '500 Internal Server Error' }
      # end

      # Home page.
      get '/' do
        erb :index, layout: :simple_layout, locals: { title: 'Home',
                              description_error: ""
                             }
      end

      # Home Page.
      post '/' do
        #test for existence of iac
        form do
          field :iac, present: true
        end

        if form.failed?
          action = "/"
          erb :index, layout: :simple_layout, locals: { title: "Home",
                                description_error: "Internet Access Code Required"
                              }
        else
          iac = "#{params[:iac]}"
          iac_response = []
          RestClient.get("http://#{settings.frame_service_host}:#{settings.frame_service_port}/questionnaires/iac/#{iac}") do |response, _request, _result, &_block|
          iac_response = JSON.parse(response)
          if response.code == 404
            erb :index, layout: :simple_layout, locals: { title: "Home",
                                  description_error: "Invalid Internet Access Code"
                                }
          else

            if !iac_response['responseDateTime'].nil?
              erb :index, layout: :simple_layout, locals: { title: "Home",
                                    description_error: "Questionnaire has been completed"
                                  }
            else
              payload = {
                          :user_id => iac_response['iac'],
                          :ru_ref => '7897897J',
                          :ru_name  => '',
                          :eq_id  => '678',
                          :collection_exercise_sid  => '789',
                          :period_id  => '',
                          :period_str  => '',
                          :ref_p_start_date  => '',
                          :ref_p_end_date  => '',
                          :employment_date  => '',
                          :trad_as  => '',
                          :form_type  => '',
                          :return_by  => 'YYYY-MM-DD',
                          :iat => '1458047712',
                          :exp => '1458057712'
                        }

              # IMPORTANT: set nil as password parameter
              token = JWT.encode payload, nil, 'none'

              logger.info token

              #url = "https://#{settings.eq_service_host}/session?token=#{token}"
              url = "http://www.google.co.uk"
              redirect url

            end
          end
        end


        end
      end


      # Show Respondent help
      get '/help' do
        erb :help, locals: { title: 'Help' }
      end




      use Rack::ETag           # Add an ETag
      use Rack::ConditionalGet # Support caching
      use Rack::Deflater       # GZip
    end
  end
end
