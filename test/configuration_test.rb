require 'test/unit'

require_relative '../lib/configuration'

class ConfigurationTest < Test::Unit::TestCase
  def setup
    ENV['RESPONDENT_HOME_EQ_HOST']                      = 'eQ host'
    ENV['RESPONDENT_HOME_EQ_PORT']                      = 'eQ port'
    ENV['RESPONDENT_HOME_IAC_ATTEMPTS_EXPIRATION_SECS'] = 'IAC attempts expiration secs'
    ENV['RESPONDENT_HOME_IAC_SERVICE_HOST']             = 'IAC service host'
    ENV['RESPONDENT_HOME_IAC_SERVICE_PORT']             = 'IAC service port'
    ENV['RESPONDENT_HOME_LOCALE']                       = 'Locale'
    ENV['RESPONDENT_HOME_MAX_IAC_ATTEMPTS']             = 'Max IAC attempts'
    ENV['RESPONDENT_HOME_REDIS_HOST']                   = 'Redis host'
    ENV['RESPONDENT_HOME_REDIS_PORT']                   = 'Redis port'
    ENV['RESPONDENT_HOME_REDIS_PASSWORD']               = 'Redis password'
    @configuration = Configuration.new(ENV)
  end

  def test_eq_host
    assert_equal 'eQ host', @configuration.eq_host
  end

  def test_eq_port
    assert_equal 'eQ port', @configuration.eq_port
  end

  def test_iac_attempts_expiration_secs
    assert_equal 'IAC attempts expiration secs', @configuration.iac_attempts_expiration_secs
  end

  def test_iac_service_host
    assert_equal 'IAC service host', @configuration.iac_service_host
  end

  def test_iac_service_port
    assert_equal 'IAC service port', @configuration.iac_service_port
  end

  def test_locale
    assert_equal 'Locale', @configuration.locale
  end

  def test_max_iac_attempts
    assert_equal 'Max IAC attempts', @configuration.max_iac_attempts
  end

  def test_redis_host
    assert_equal 'Redis host', @configuration.redis_host
  end

  def test_redis_port
    assert_equal 'Redis port', @configuration.redis_port
  end

  def test_redis_password
    assert_equal 'Redis password', @configuration.redis_password
  end
end
