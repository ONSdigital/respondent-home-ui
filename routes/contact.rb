get '/individualquestionnaire' do
  erb :contact, locals: { title: I18n.t('request_an_individual_questionnaire'),
                          host: settings.host,
                          built: @built,
                          commit: @commit,
                          locale: @locale,
                          environment: settings.environment,
                          analytics_account: settings.analytics_account }
end
