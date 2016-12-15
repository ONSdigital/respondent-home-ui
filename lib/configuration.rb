# Simple class to centralise access to configuration.
class Configuration
  attr_reader :analytics_account,
              :eq_host,
              :eq_port,
              :eq_protocol,
              :iac_service_host,
              :iac_service_port,
              :iac_service_protocol,
              :iac_service_user,
              :iac_service_password,
              :notify_api_key,
              :notify_email_address,
              :notify_template_id

  # rubocop:disable Metrics/AbcSize
  def initialize(env)
    @analytics_account    = env['RESPONDENT_HOME_ANALYTICS_ACCOUNT']
    @eq_host              = env['RESPONDENT_HOME_EQ_HOST']
    @eq_port              = env['RESPONDENT_HOME_EQ_PORT']
    @eq_protocol          = env['RESPONDENT_HOME_EQ_PROTOCOL']
    @iac_service_host     = env['RESPONDENT_HOME_IAC_SERVICE_HOST']
    @iac_service_port     = env['RESPONDENT_HOME_IAC_SERVICE_PORT']
    @iac_service_protocol = env['RESPONDENT_HOME_IAC_SERVICE_PROTOCOL']
    @iac_service_user     = env['RESPONDENT_HOME_IAC_SERVICE_USER']
    @iac_service_password = env['RESPONDENT_HOME_IAC_SERVICE_PASSWORD']
    @notify_api_key       = env['RESPONDENT_HOME_NOTIFY_API_KEY']
    @notify_email_address = env['RESPONDENT_HOME_NOTIFY_EMAIL_ADDRESS']
    @notify_template_id   = env['RESPONDENT_HOME_NOTIFY_TEMPLATE_ID']
  end
  # rubocop:enable Metrics/AbcSize
end
