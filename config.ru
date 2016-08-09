require 'rubygems'
require 'bundler'

Bundler.require

require_relative 'routes/home'
require_relative 'routes/error'

require 'rack/etag'
require 'rack/conditionalget'
require 'rack/deflater'

use Rack::ETag            # Add an ETag
use Rack::ConditionalGet  # Support caching
use Rack::Deflater        # GZip

run Sinatra::Application
