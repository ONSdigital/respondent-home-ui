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

## Running
To run this application in development using its [Rackup](http://rack.github.io/) file use:

  `bundle exec rackup config.ru` (the `config.ru` may be omitted as Rack looks for this file by default)

and access using [http://localhost:9292](http://localhost:9292)

## Running Using the Mock Backend
This project includes a Sinatra application that provide a mock version of the Internet Access Code web service. To run it, edit your hosts file so that `collect-server` uses 127.0.0.1. Then run:

  `./run.sh` from within the `mock` directory. This is a shell script that starts the mock web service in the background. Use Ctrl + C to terminate it. The output from the background process is written to `mock/nohup.out`. This file can be deleted if not required.

Start the user interface normally as described above. Use `fb74 7cq7 25lj` as a test IAC that is no longer valid because the questionnaire has already been submitted. Use the IACs in the table below as valid test IACs for each question set:

<table>
  <thead>
    <tr>
      <th>IAC</th>
      <th>Question Set</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>wsyc yxw9 kn5g</code></td>
      <td>H1</td>
      <td>Household questionnaire for England without sexual ID</td>
    </tr>
    <tr>
      <td><code>h479 nl7y x9w2</code></td>
      <td>H1S</td>
      <td>Household questionnaire for England with sexual ID</td>
    </tr>
    <tr>
      <td><code>ssn4 bqkg n7gl</code></td>
      <td>H2</td>
      <td>Household questionnaire for Wales (in English) without sexual ID</td>
    </tr>
    <tr>
      <td><code>b55s wlzg w778</code></td>
      <td>H2S</td>
      <td>Household questionnaire for Wales (in English) with sexual ID</td>
    </tr>
    <tr>
      <td><code>4kyz nty4 fw3s</code></td>
      <td>I1</td>
      <td>Individual questionnaire for England without sexual ID</td>
    </tr>
    <tr>
      <td><code>5p9y 7rdc 3t3q</code></td>
      <td>I1S</td>
      <td>Individual questionnaire for England with sexual ID</td>
    </tr>
    <tr>
      <td><code>wn9k btyp zth8</code></td>
      <td>I2</td>
      <td>Individual questionnaire for Wales (in English) without sexual ID</td>
    </tr>
    <tr>
      <td><code>xmyv jwjv t5yc</code></td>
      <td>I2S</td>
      <td>Individual questionnaire for Wales (in English) with sexual ID</td>
    </tr>
    <tr>
      <td><code>yr94 73ty n7qk</code></td>
      <td>HOTEL</td>
      <td>Hotel questionnaire</td>
    </tr>
  </tbody>
</table>

## Environment Variables
The environment variables below must be provided:

```
RESPONDENT_HOME_ANALYTICS_ACCOUNT
RESPONDENT_HOME_EQ_HOST
RESPONDENT_HOME_EQ_PORT
RESPONDENT_HOME_EQ_PROTOCOL
RESPONDENT_HOME_IAC_SERVICE_HOST
RESPONDENT_HOME_IAC_SERVICE_PORT
RESPONDENT_HOME_IAC_SERVICE_PROTOCOL
RESPONDENT_HOME_NOTIFY_API_KEY
RESPONDENT_HOME_NOTIFY_TEMPLATE_ID
```

The script `/env.sh` can be sourced in development to set these variables with reasonable defaults.

## Running on Cloud Foundry
Before pushing the application bundle, package the gems, this is required as the Cloud Foundry instance cannot see the private RubyGems server where the `iac-validator` gem is hosted:

```
bundle package --all
cf push
```

### Cloud Foundry Troubleshooting
You may get an error message saying `The host is taken: respondent-home-ui`. This is caused because an instance of the app is already running and using the host name. In this case edit the `manifest.yml` file and change the host value.
