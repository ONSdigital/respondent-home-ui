require 'redis'

# Class to manage the number of IAC authentication attempts. Uses Redis as a
# backing store.
class AuthenticationAttemptLimiter
  KEY_PREFIX = 'respondent.home:auth.attempt:'

  def initialize(redis_host, redis_port, max_attempts, ip_address)
    @redis_host   = redis_host
    @redis_port   = redis_port
    @max_attempts = max_attempts
    @key          = "#{KEY_PREFIX}#{ip_address}"
    attempts = attempt_counter_cache.get(@key).to_i || 0
    attempt_counter_cache.set(@key, attempts) if attempts.zero?
  end

  def attempt!
    attempts = attempt_counter_cache.get(@key).to_i + 1
    attempt_counter_cache.set(@key, attempts)
  end

  def max_attempts?
    attempt_counter_cache.get(@key).to_i >= @max_attempts.to_i - 1
  end

  private

  def attempt_counter_cache
    @attempt_counter_cache ||= Redis.new(host: @redis_host, port: @redis_port)
  end
end
