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

    # See http://regexlib.com/REDetails.aspx?regexp_id=592
    field :mobile,       present: true, regexp: %r{^(\+44\s?7\d{3}|\(?07\d{3}\)?)\s?\d{3}\s?\d{3}$}
  end

  if form.failed?
    output = erb :contact, locals: { title: I18n.t('request_an_individual_questionnaire'),
                                     host: settings.host,
                                     built: @built,
                                     commit: @commit,
                                     locale: @locale,
                                     environment: settings.environment,
                                     analytics_account: settings.analytics_account }
    fill_in_form(output)
  else
    erb :contact_success, locals: { title: I18n.t('request_an_individual_questionnaire'),
                                    host: settings.host,
                                    built: @built,
                                    commit: @commit,
                                    locale: @locale,
                                    environment: settings.environment,
                                    analytics_account: settings.analytics_account }
  end
end
