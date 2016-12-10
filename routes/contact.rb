get '/individualquestionnaire' do
  erb :contact, locals: { title: I18n.t('request_an_individual_questionnaire'),
                          host: settings.host,
                          built: @built,
                          commit: @commit,
                          locale: @locale,
                          environment: settings.environment,
                          analytics_account: settings.analytics_account }
end

post '/individualquestionnaire' do
  form do
    field :first_name,   present: true
    field :last_name,    present: true
    field :building,     present: true
    field :street,       present: true
    field :town_or_city, present: true
    field :postcode,     present: true, filters: :upcase
    field :mobile,       present: true, length: 7..14
  end

  if form.failed?
    puts form.failed_fields.class
    output = erb :contact, locals: { title: I18n.t('request_an_individual_questionnaire'),
                                     host: settings.host,
                                     built: @built,
                                     commit: @commit,
                                     locale: @locale,
                                     environment: settings.environment,
                                     analytics_account: settings.analytics_account }
    fill_in_form(output)
  else
  end
end
