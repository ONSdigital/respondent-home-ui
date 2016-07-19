Respondent Home Ruby Web Application
========================================

This Ruby Sinatra application allows users to validate their IAC and forwards to eQ

Prerequisites
-------------

The application's `config.yml` configuration file references the Java web services using a `collect-server` name which needs to be present in your hosts file. Install the RubyGems the application depends on by running `bundle install`.

Running
-------

To run this project in development using its [Rackup](http://rack.github.io/) file use:

  `bundle exec rackup config.ru` (the `config.ru` may be omitted as Rack looks for this file by default)

and access using [http://localhost:9292](http://localhost:9292)

Running Using the Mock Backend
------------------------------

This project includes a Sinatra applications that provide mock versions of the caseframeservice. To run them, edit your hosts file so that `collect-server` uses 127.0.0.1. Then run:

  `bundle exec rackup -p 8178` from within the `mock\caseframeservice` directory

Start the user interface normally as described above.
