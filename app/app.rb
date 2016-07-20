require_relative './routes/base'

module Beyond
  class App < Sinatra::Application
    use Routes::Base
  end
end
