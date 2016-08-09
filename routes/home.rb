require 'sinatra'
require 'sinatra/content_for2'
require 'sinatra/flash'
require 'sinatra/formkeeper'
require 'rest_client'
require 'json'
require 'yaml'
require 'json/jwt'
require 'jwe'
require 'openssl'
require 'base64'

SESSION_EXPIRATION_PERIOD = 60 * 60 * 6

# Load various settings from a configuration file.
config = YAML.load_file(File.join(__dir__, '../config.yml'))
set :case_service_host, config['case-webservice']['host']
set :case_service_port, config['case-webservice']['port']
set :eq_service_host, config['eq-service']['host']
set :eq_service_port, config['eq-service']['port']

# Expire sessions after SESSION_EXPIRATION_PERIOD minutes of inactivity.
use Rack::Session::Cookie, key: 'rack.session', path: '/',
                           secret: 'f089802942494ca9a7250a849d8d8c0c',
                           expire_after: SESSION_EXPIRATION_PERIOD

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
    RestClient.get("http://#{settings.case_service_host}:#{settings.case_service_port}/questionnaires/iac/#{iac}") do |response, _request, _result, &_block|
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

        priv_key = "-----BEGIN RSA PRIVATE KEY-----\nProc-Type: 4,ENCRYPTED\nDEK-Info: AES-256-CBC,C2C5740E6DA1DD915CA90CFFCBDFA5B2\n\nnlAOzfOUcrksZS2H0WLE27ME/wpuDo8rimRBxA++EHe+2HJsXyiNz+PRPHPOIvcW\nlGtPgLcfwT9A+pwico0s1u0N8/XQC21640r30xBQSW6Y+msPLoibnvl6bkDO0z/z\nx+mqCQvPTQEpJwwbtE8wFbrs74P0y6EUFIu8m8yPBg9Fmt8noAuR227l5tg/TLga\nHMFYT5mFO7g+oJvtJhOxXcCNf3EcoRQOlap9PHq2daVSTXy+qCTVe5AVDIlufidp\nfl4qGAqu5z2JbI8dsm+WJGtvqGacNoLOHsKHFGx/Qgy5em/NPAf9ak5fgjxQrrK1\nUWh+EymVsSQKN8MXPWYSzthSdoYAUuWu1iaDbcJw8CWU2vfmgXMxjTPUvsx0wRUX\n4tUfNtgqxcIsh1bH3MtcCeqxtyUOG96f2TGCx6gofUiKxwMoBzk3HqdgwexvZW1L\n64xgbY02AvztjxD8KFNWXQgji9mKorplqCIugpj67oRIwVOwdzfebiLk5eFb31Jj\nRZumElCCo2UtQe/fAqebBAC2CtaMuSBTozmHNPx9DDEGVQH6i/ZZHTHCvFG1+MJS\nPyTRQZnS4qnj+b7ObBNvAhSPsUD6hKI0yV3k1I3P+Hi1syMMIFKUwahzUReLF5le\nCdT4rMgrpHDyw5QUH5IjHzc0AXxoomM5UaUkk65E+MHU3nq37E7ExE6AFTdqmP4t\nI67Ed+bHNe6qxweDtuuc84Ok24k8OxRoZchrhFytWpk1lkijGUb/fRdmS4/6HiKJ\nRgkZ+VHi/FQN3/fedzfHouWYKaGKI51MEQfB7cSL8g13MchhGVOmu9TG6+F1/qRc\ndNil/8PE/cafxFEImW1v//ycLx0k/njfXyi/U2Vk8+WEDEtPe1fsF0F+vdnRH+l3\nzWsPtgqRqVAWZxn28xN8xNA9+iaoKH869/OVRDbmeU1tNQaSnCE3Ltkrg5Qoc8r5\nnPEviH812mnKkS299NVQFHbBSN2WDrf27gYKDn0ajSBo9GBeQJQOPTGWkMlHnOFB\nALphV1Ul2APJih7rgcHh6RubgN6X3EfFCL5VzSlpqGnYp9Ov1+U0iLjyfMWgLOd8\npXyIOl9qMJUZchjLsFXCj2u/SGuAu2ojMnG+0UFxYnx+f9l6UcUvEAYJIJop6XS9\ntB5rgsqQwYAB3N7yQ/C12fVc6qITffRxqBaGEe9yPFZO5XmUgn/oNtJuArSPBAIe\nInZI1TWbvAeVYfDQEJDsM1ND0X17MAPghQXH4nVavJydGbUY5sg9QJF2BBP6sT9Y\nzvgYUD5RZfzwuZOfdy46fv3VmqR2fYKuj1zVXFqGiINFsQb6airDt/11NJ0p8avo\n9X/eR20/uU6gtk5ABF2U3zepa3NheMhZJUmHysmYKiYwO6sJ1XTpAjNhmmLcOsEI\nXXCtQwd8uNYVzxSlbCSB3EQ841Ix9Z1+z/qUsFM01dX882It7qP/M7AdhogEYaPR\nZNMk0igVzh9T+6ErSOngoug0nLRqZsKlMhC7RNskMpIqt8iGLGnjLRT+4adwvCUW\nERd/A2RoDdedhgV49v9mYUWtENxGOr1VmOG98FzdmfUqwxNpukfhF9fz7iCB+Bnk\n-----END RSA PRIVATE KEY-----"
        private_key  = OpenSSL::PKey::RSA.new(priv_key, 'digitaleq')
        pub_key = "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvZzMraB96Wd1zfHS3vW3\n0pi6IOu92MlIwdH/L6CTuzYnG4PACKT8FZonLw0NYBqh8p4vWS8xtNHNjTWua/FF\nz//Nkqz+9HfwViNje2Y5L6m3K/7raA0kUsWD1f6X7/LIJfkCEctCEj9q19+cX30h\nTlxdtYnEb9HbUZkg7dXAtnikozlE/ZZSponq7K00h3Uh9goxQIavcK1QI8pw5V+T\n8V8Ue7k98W8LpbYQWm7FPOZayu1EoJWUZefdOlYAdeVbDS4tjrVF+3za+VX3q73z\nJEfyLEM0zKrkQQ796gfYpkzDYwJvkiW7fb2Yh1teNHpFR5tozzMwUxkREl/TQ4U1\nkwIDAQAB\n-----END PUBLIC KEY-----"
        public_key = OpenSSL::PKey::RSA.new(pub_key)

        cek =  Random.new.bytes(32)
        iv  =  Random.new.bytes(12)


        jwt = JSON::JWT.new(payload)
        jwt.kid = 'EDCRRM'
        jwt.alg = :RS256


        jws = jwt.sign(private_key, :RS256)


        # encrypt the token
        eqtoken = jws.encrypt(public_key,'RSA-OAEP', :A256GCM).to_s

        logger.info eqtoken
        url = "http://#{settings.eq_service_host}:#{settings.eq_service_port}/session?token=" + eqtoken
        redirect url
      end
    end
  end
end

get '/help' do
  erb :help, layout: :simple_layout, locals: { title: 'Help' }
end
