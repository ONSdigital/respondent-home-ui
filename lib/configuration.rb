# Simple class to centralise access to configuration.
class Configuration
  attr_reader :analytics_account,
              :eq_host,
              :eq_port,
              :iac_attempts_expiration_secs,
              :iac_service_host,
              :iac_service_port,
              :locale,
              :max_iac_attempts,
              :redis_host,
              :redis_port,
              :redis_password

  # rubocop:disable Metrics/AbcSize, Style/GuardClause
  def initialize(env)
    @analytics_account            = env['RESPONDENT_HOME_ANALYTICS_ACCOUNT']
    @eq_host                      = env['RESPONDENT_HOME_EQ_HOST']
    @eq_port                      = env['RESPONDENT_HOME_EQ_PORT']
    @iac_attempts_expiration_secs = env['RESPONDENT_HOME_IAC_ATTEMPTS_EXPIRATION_SECS']
    @iac_service_host             = env['RESPONDENT_HOME_IAC_SERVICE_HOST']
    @iac_service_port             = env['RESPONDENT_HOME_IAC_SERVICE_PORT']
    @locale                       = env['RESPONDENT_HOME_LOCALE']
    @max_iac_attempts             = env['RESPONDENT_HOME_MAX_IAC_ATTEMPTS']
    @redis_host                   = env['RESPONDENT_HOME_REDIS_HOST']
    @redis_port                   = env['RESPONDENT_HOME_REDIS_PORT']
    @redis_password               = env['RESPONDENT_HOME_REDIS_PASSWORD']

    if env['VCAP_SERVICES']
      vcap_redis_credentials = JSON.parse(env['VCAP_SERVICES'])['p-redis'].first['credentials']
      @redis_host     = vcap_redis_credentials['host']
      @redis_port     = vcap_redis_credentials['port']
      @redis_password = vcap_redis_credentials['password']
    end
  end
  # rubocop:enable Metrics/AbcSize, Style/GuardClause
end
