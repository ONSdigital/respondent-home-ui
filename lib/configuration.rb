# Simple class to centralise access to configuration.
class Configuration
  attr_reader :analytics_account,
              :aws_s3_bucket,
              :eq_host,
              :eq_port,
              :eq_protocol,
              :iac_service_host,
              :iac_service_port,
              :iac_service_protocol,
              :iac_service_user,
              :iac_service_password

  def initialize(env)
    @analytics_account    = env['RESPONDENT_HOME_ANALYTICS_ACCOUNT']
    @aws_s3_bucket        = env['AWS_S3_BUCKET']
    @eq_host              = env['RESPONDENT_HOME_EQ_HOST']
    @eq_port              = env['RESPONDENT_HOME_EQ_PORT']
    @eq_protocol          = env['RESPONDENT_HOME_EQ_PROTOCOL']
    @iac_service_host     = env['RESPONDENT_HOME_IAC_SERVICE_HOST']
    @iac_service_port     = env['RESPONDENT_HOME_IAC_SERVICE_PORT']
    @iac_service_protocol = env['RESPONDENT_HOME_IAC_SERVICE_PROTOCOL']
    @iac_service_user     = env['RESPONDENT_HOME_IAC_SERVICE_USER']
    @iac_service_password = env['RESPONDENT_HOME_IAC_SERVICE_PASSWORD']
  end
end
