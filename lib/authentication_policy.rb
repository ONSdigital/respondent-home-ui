require 'redis'
require 'json'

Attempt = Struct.new(:count, :time)

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
    attempt = fetch_attempt
    attempt.count >= @max_attempts.to_i - 1
  end

  def failed_attempt!
    attempt = fetch_attempt
    attempt.count += 1
    attempt.time = Time.now
    store_attempt(attempt)
  end

  private

  def fetch_attempt
    attempt_json = redis.get(@key)

    if attempt_json.nil?
      attempt = Attempt.new(0, Time.now)
      store_attempt(attempt)
      return attempt
    end

    # See http://stackoverflow.com/a/14943188
    Attempt.new(*JSON[attempt_json].values_at('count', 'time'))
  end

  def redis
    @redis ||= Redis.new(host: @redis_host, port: @redis_port)
  end

  def store_attempt(attempt)
    # See http://stackoverflow.com/a/28313500
    redis.set(@key, attempt.to_h.to_json)
  end
end
