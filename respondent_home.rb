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

        # IMPORTANT: set nil as password parameter
        # sign the token
        header = {typ: 'jwt', kid: 'EDCRRM', alg: 'RS256'}

        jws = JSON::JWT.new(payload).sign(private_key, header)

        # jws = JWT.sign(payload, header, private_key)

        # encrypt the token
        token = JWE.encrypt(jws, public_key, enc: 'A256GCM')

        logger.info token

        # token = 'eyJhbGciOiJSU0EtT0FFUCIsImVuYyI6IkEyNTZHQ00ifQ.SIhyPiJLnGZIC-fey_4nhATLfbg5ErUPeeWQKV7-PYJJWRkJMRJ2cIQw7BDTip7GTh0dMC4h-eee04hrWJzyag6U55FE8gKYxvcBEtluDQtMLKOGnEfb7tfQKPzVEqkSDi3x7qjERoPhbpw6Nh8vG6-_WY1nkGWAaZUbgk3TQ3Pw7COay9ttPPmv5Ej6ne00sVVHN_D1iRJ_9ccz3-yyhTPC0lZFjbGbiiV2TneEiJ9HSiaJzV74raYQO4gCGD2CYE2AZv5rMUtzb7eMqLbfAFpxLXq-8MDqQzVJSY6gjkVtlUY5lFEswIKIIC6xUnigM24LKpfVZFK8u0kWGlI4uQ.Qn_IYXWHDmReeo0V.LlCGYnKNKO7FZe57iBWDsfj8hnidWGpHdXWyAEQXo_o7zfPLrRhCUqujJOcSDcFAT8s5e3YZt4ff0o2c-8CbqAga4yXHYxy6PRSC-hORnDILy2dvUXSQUdkkvkdWKqeIEZkU7nyuwH3lh8AAbAPok1luCeFdpyVPc_tKiFQQv24o8x8qGGWYOJvMBqbASLbsR1S-y4JQ5EbJGDLXDbi22FoID63wXwlvVVHerGrSJgz2DKgu-GrMEIGSkd5POxjbAtbyyFCKmiM5hhzNYK8oREC7nAk3nbyf0VtMH4FUpfqqZtzTWLkAGYPMt2F2LSiU9yTAgXJcsAoAxlsc0_SGuw0TdPoI7iVZf8vFuyyg2Wn6V6ycPphYSnf12flsa5b5514omTuGeLSBaz8vA-Hr4Qnm2RFW40OJd6KdSF_NY3TamY6EYUoTUv278AbuueEeje_BFXEg6t9tOwEwmy2YE89x9NSyXN_SMz1kRB-ryVeWf3SoHY_pdmsP1V-69ahTqu1fgMicVIoHydRDFce3U-UcvnD-lvS10jvC-EyDUnbIY3WhUF9cDakruTLp6_5dZreji5GP5meIRkIZADkXX-P2V9OXivV3rZfGtz3zx0Vp25bKoANd4Djffci_eQcEzXpILH9ySbVUT3k2ZFfMuGeqDpBZq5vh9UQnlp34nKJjldsDCkkuz9yMSENYC3ZzRDTloRAalnk6j3_WiCLfaqxwoE_GEJ4GeEmQFLvcrAaH1-DFY_MgvDWVw_A6EAA2q_CN9Uzvbycqah2WFEU1IzmZrzv_Xz92T_mbp2JGTNMwXj4i7pWx8t3GtWhJms0cA4srMVc6ptOASdLJWrv64-wp9QbJ8tYp5C4j-L7Sk3Qwz6kZha70i1kS5Eq7hMtzCNJl4syU3jF3UthLmLMlTEYKIKmSsepwhrIFEjIaDsJCmiEGdRRi0KbIwRqjV_uRAuMstGwBq150sEoljE71o4-1mRhVKkwFFbukdJTto8_qKuK4LxB2do5Z2kehVyl44-5OHLFKgrXcy6Dl6knkBQN9rS72bNQPLH1eqAV1gqHcvmoDsJ-rwYwRxPrueCNCRUekvX_epwEl-kq54jbGfAPvFKm4Cb7n170k.PG2X3zUnILf1PWuiWuITAw'

        url = "http://#{settings.eq_service_host}:#{settings.eq_service_port}/session?token=#{token}"
        redirect url
      end
    end
  end
end

get '/help' do
  erb :help, layout: :simple_layout, locals: { title: 'Help' }
end
