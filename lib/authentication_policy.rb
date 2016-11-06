require 'redis'

# Class to manage the number of IAC authentication attempts.
class AuthenticationPolicy
  KEY_PREFIX = 'respondent.home:auth.attempt:'.freeze

  def initialize(redis_host, redis_port, max_attempts, ip_address)
    @redis_host   = redis_host
    @redis_port   = redis_port
    @max_attempts = max_attempts
    @key          = "#{KEY_PREFIX}#{ip_address}"
  end

  def client_blocked?
    count = fetch_count
    count >= @max_attempts.to_i - 1
  end

  def failed_attempt!
    redis.multi do |multi|
      multi.incr(@key)
      multi.expire(@key, 20)
    end
  end

  private

  def fetch_count
    count = redis.get(@key)
    return 0 if count.nil?
    count.to_i
  end

  def redis
    @redis ||= Redis.new(host: @redis_host, port: @redis_port)
  end
end
