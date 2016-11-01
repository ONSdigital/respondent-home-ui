require 'redis'

# Class to manage the number of IAC authentication attempts. Uses Redis as a
# backing store.
class AuthenticationAttemptLimiter
  def initialize(redis_host, redis_port, max_attempts, ip_address)
    @redis_host   = redis_host
    @redis_port   = redis_port
    @max_attempts = max_attempts
    @ip_address   = ip_address
    attempts = attempt_counter_cache.get(@ip_address).to_i || 0
    attempt_counter_cache.set(@ip_address, attempts) if attempts.zero?
  end

  def attempt!
    attempts = attempt_counter_cache.get(@ip_address).to_i + 1
    attempt_counter_cache.set(@ip_address, attempts)
  end

  def max_attempts?
    attempt_counter_cache.get(@ip_address).to_i >= @max_attempts.to_i - 1
  end

  private

  def attempt_counter_cache
    @attempt_counter_cache ||= Redis.new(host: @redis_host, port: @redis_port)
  end
end
