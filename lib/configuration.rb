# Simple class to centralise access to configuration.
class Configuration
  attr_reader :eq_host, :eq_port, :iac_service_host, :iac_service_port, :locale,
              :max_iac_attempts, :redis_host, :redis_port

  def initialize(env)
    @eq_host          = env['RESPONDENT_HOME_EQ_HOST']
    @eq_port          = env['RESPONDENT_HOME_EQ_PORT']
    @iac_service_host = env['RESPONDENT_HOME_IAC_SERVICE_HOST']
    @iac_service_port = env['RESPONDENT_HOME_IAC_SERVICE_PORT']
    @locale           = env['RESPONDENT_HOME_LOCALE']
    @max_iac_attempts = env['RESPONDENT_HOME_MAX_IAC_ATTEMPTS']
    @redis_host       = env['RESPONDENT_HOME_REDIS_HOST']
    @redis_port       = env['RESPONDENT_HOME_REDIS_PORT']
  end
end
