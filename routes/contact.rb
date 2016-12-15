get '/individualquestionnaire' do
  erb :contact, locals: { title: I18n.t('contact_heading1'),
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
    field :town,         present: true

    # See http://regexlib.com/REDetails.aspx?regexp_id=260
    field :postcode,     present: true, filters: :upcase, regexp: /^([A-PR-UWYZ0-9][A-HK-Y0-9][AEHMNPRTVXY0-9]?[ABEHMNPRVWXY0-9]? {0,2}[0-9][ABD-HJLN-UW-Z]{2}|GIR 0AA)$/

    # See http://regexlib.com/REDetails.aspx?regexp_id=592
    field :mobile,       present: true, regexp: /^(\+44\s?7\d{3}|\(?07\d{3}\)?)\s?\d{3}\s?\d{3}$/
  end

  if form.failed?
    output = erb :contact, locals: { title: I18n.t('contact_heading1'),
                                     host: settings.host,
                                     built: @built,
                                     commit: @commit,
                                     locale: @locale,
                                     environment: settings.environment,
                                     analytics_account: settings.analytics_account }
    fill_in_form(output)
  else
    contact_data = {

      # Need to get the correct client IP address when behind a load balancer.
      client_ip:  request.env['HTTP_X_FORWARDED_FOR'] || request.ip,
      first_name: h(form[:first_name]),
      last_name:  h(form[:last_name]),
      building:   h(form[:building]),
      street:     h(form[:street]),
      town:       h(form[:town]),
      county:     h(form[:county]),
      postcode:   h(form[:postcode]),
      mobile:     h(form[:mobile])
    }

    EmailJob.perform_async(settings.notify_email_address, contact_data,
                           settings.notify_template_id, settings.notify_api_key)

    erb :contact_success, locals: { title: I18n.t('contact_success_heading1'),
                                    host: settings.host,
                                    built: @built,
                                    commit: @commit,
                                    locale: @locale,
                                    environment: settings.environment,
                                    analytics_account: settings.analytics_account }
  end
end
