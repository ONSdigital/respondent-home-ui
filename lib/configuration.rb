# Simple class to centralise access to configuration.
class Configuration
  attr_reader :analytics_account,
              :eq_host,
              :eq_port,
              :eq_protocol,
              :iac_service_host,
              :iac_service_port,
              :locale

  def initialize(env)
    @analytics_account            = env['RESPONDENT_HOME_ANALYTICS_ACCOUNT']
    @eq_host                      = env['RESPONDENT_HOME_EQ_HOST']
    @eq_port                      = env['RESPONDENT_HOME_EQ_PORT']
    @eq_protocol                  = env['RESPONDENT_HOME_EQ_PROTOCOL']
    @iac_service_host             = env['RESPONDENT_HOME_IAC_SERVICE_HOST']
    @iac_service_port             = env['RESPONDENT_HOME_IAC_SERVICE_PORT']
    @locale                       = env['RESPONDENT_HOME_LOCALE']
  end
end
