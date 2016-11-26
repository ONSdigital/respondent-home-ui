# Respondent Home Ruby Web Application
Respondent Home is part of ONS's Survey Data Collection platform. It allows users to validate their Internet Access Code (IAC) and forwards
them to the [ONS eQ Survey Runner](https://github.com/ONSdigital/eq-survey-runner) upon successful validation.

![The ONS Survey Data Collection platform](/images/sdc_platform.png?raw=true)

This repository contains the Ruby [Sinatra](http://www.sinatrarb.com/) application that is the user interface for the Respondent Home product.

## Prerequisites
Install the RubyGems the application depends on by running `bundle install`. Note that this application depends on a private `iac-validator` RubyGem for performing IAC validation. This gem is only used in one place within `routes/home.rb`:

```ruby
unless InternetAccessCodeValidator.new(iac).valid?
  ...
end
```

A [Redis](http://redis.io/) server is required to keep track of the number of attempts a client makes to use an IAC. Specify the Redis host and port using the `RESPONDENT_HOME_REDIS_HOST` and `RESPONDENT_HOME_REDIS_PORT` environment variables as listed in the **Environment Variables** section below.

## Running
To run this application in development using its [Rackup](http://rack.github.io/) file use:

  `bundle exec rackup config.ru` (the `config.ru` may be omitted as Rack looks for this file by default)

and access using [http://localhost:9292](http://localhost:9292)

## Running Using the Mock Backend
This project includes a Sinatra application that provide a mock version of the Internet Access Code web service. To run it, edit your hosts file so that `collect-server` uses 127.0.0.1. Then run:

  `./run.sh` from within the `mock` directory. This is a shell script that starts the mock web service in the background. Use Ctrl + C to terminate it. The output from the background process is written to `mock/nohup.out`. This file can be deleted if not required.

Start the user interface normally as described above. Use **q8ms h8vd nj6d** as a test IAC that is no longer valid because the questionnaire has already been submitted. Use **yxf4 f87d hj73** as a valid test IAC.

## Environment Variables
The environment variables below must be provided:

```
RESPONDENT_HOME_ANALYTICS_ACCOUNT
RESPONDENT_HOME_EQ_HOST
RESPONDENT_HOME_EQ_PORT
RESPONDENT_HOME_EQ_PROTOCOL
RESPONDENT_HOME_IAC_ATTEMPTS_EXPIRATION_SECS
RESPONDENT_HOME_IAC_SERVICE_HOST
RESPONDENT_HOME_IAC_SERVICE_PORT
RESPONDENT_HOME_LOCALE = (en|cy)
RESPONDENT_HOME_MAX_IAC_ATTEMPTS
RESPONDENT_HOME_NOTIFY_API_KEY
RESPONDENT_HOME_NOTIFY_TEMPLATE_ID
RESPONDENT_HOME_REDIS_HOST
RESPONDENT_HOME_REDIS_PORT
RESPONDENT_HOME_REDIS_PASSWORD
```

The script `/env.sh` can be sourced in development to set these variables with reasonable defaults.

## Running on Cloud Foundry
In order to run on Cloud Foundry a Redis service must first be created and then bound to the application:

```
 cf create-service p-redis dedicated-vm respondent-home-ui-redis
 cf bind-service respondent-home-ui respondent-home-ui-redis
```

Before pushing the application bundle, package the gems, this is required as the Cloud Foundry instance cannot see the private RubyGems server where the `iac-validator` gem is hosted:

```
bundle package --all
cf push
```

## Cloud Foundry Troubleshooting
You may get an error message saying `The host is taken: respondent-home-ui`. This is caused because an instance of the app is already running and using the host name. In this case edit the `manifest.yml` file and change the host value.
