require 'rubygems'
require 'sinatra'

require_relative 'routes/case'

require 'rack/etag'
require 'rack/conditionalget'
require 'rack/deflater'

use Rack::ETag            # Add an ETag
use Rack::ConditionalGet  # Support caching
use Rack::Deflater        # GZip

run Sinatra::Application
