require 'rack/etag'
require 'rack/conditionalget'
require 'rack/deflater'

require_relative './routes/base'

# Open up various built-in classes to add new convenience methods.
class Object

  # An object is blank if it's false, empty, or a whitespace string. For example, '', ' ', nil, [], and {} are all blank.
  def blank?
    respond_to?(:empty?) ? !!empty? : !self
  end

  # An object is present if it's not blank.
  def present?
    !blank?
  end
end

class Date
  def self.string_to_epoch_time(str)
    DateTime.parse(str).to_time.utc.to_i
  end
end

class Integer
  def to_comma_formatted
    to_s.gsub(/(\d)(?=(\d\d\d)+(?!\d))/, '\\1,')
  end

  def to_date(time: true)
    if time
      Time.at(self / 1000).utc.strftime('%e %b %Y %H:%M')
    else
      Time.at(self / 1000).utc.strftime('%e %b %Y')
    end
  end

  def to_hours
    Time.at(self / 1000).utc.strftime('%H')
  end

  def to_minutes
    Time.at(self / 1000).utc.strftime('%M')
  end
end





module Beyond
  class App < Sinatra::Application
    use Routes::Base
  end
end
