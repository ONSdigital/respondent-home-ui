require 'rubygems'
require 'bundler'

Bundler.require

require_relative 'respondent_home'
run Sinatra::Application
