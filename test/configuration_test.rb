require 'test/unit'

require_relative '../lib/configuration'

class ConfigurationTest < Test::Unit::TestCase
  def setup
    ENV['RESPONDENT_HOME_ANALYTICS_ACCOUNT'] = 'Analytics account'
    ENV['RESPONDENT_HOME_EQ_HOST']           = 'eQ host'
    ENV['RESPONDENT_HOME_EQ_PORT']           = 'eQ port'
    ENV['RESPONDENT_HOME_EQ_PROTOCOL']       = 'eQ protocol'
    ENV['RESPONDENT_HOME_IAC_SERVICE_HOST']  = 'IAC service host'
    ENV['RESPONDENT_HOME_IAC_SERVICE_PORT']  = 'IAC service port'
    @configuration = Configuration.new(ENV)
  end

  def test_analytics_account
    assert_equal 'Analytics account', @configuration.analytics_account
  end

  def test_eq_host
    assert_equal 'eQ host', @configuration.eq_host
  end

  def test_eq_port
    assert_equal 'eQ port', @configuration.eq_port
  end

  def test_eq_protocol
    assert_equal 'eQ protocol', @configuration.eq_protocol
  end

  def test_iac_service_host
    assert_equal 'IAC service host', @configuration.iac_service_host
  end

  def test_iac_service_port
    assert_equal 'IAC service port', @configuration.iac_service_port
  end
end
