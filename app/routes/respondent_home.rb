module Beyond
  module Routes
    class FrameService < Base

      # Show help for Respondent Home.
      get '/help' do
        erb :help, locals: { title: 'Help' }
      end

      

    end
  end
end
