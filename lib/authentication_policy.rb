require 'redis'

# Class to manage the number of IAC authentication attempts.
class AuthenticationPolicy
  KEY_PREFIX = 'respondent.home:auth.attempt:'.freeze

  def initialize(settings, ip_address)
    @redis_host                   = settings.redis_host
    @redis_port                   = settings.redis_port
    @redis_password               = settings.redis_password
    @iac_attempts_expiration_secs = settings.iac_attempts_expiration_secs
    @max_iac_attempts             = settings.max_iac_attempts
    @key                          = "#{KEY_PREFIX}#{ip_address}"
  end

  def client_blocked?
    count = redis.get(@key) || 0
    count.to_i >= @max_iac_attempts.to_i - 1
  end

  def failed_attempt!
    redis.multi do |multi|
      multi.incr(@key)
      multi.expire(@key, @iac_attempts_expiration_secs)
    end
  end

  private

  def redis
    @redis ||= Redis.new(host: @redis_host, port: @redis_port,
                         password: @redis_password)
  end
end
