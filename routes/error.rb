error 404 do
  erb :error, locals: { title: I18n.t('not_found_heading1'),
                        locale: @locale,
                        analytics_account: settings.analytics_account,
                        user_agent: parse_user_agent }
end

error 500 do
  erb :error, locals: { title: I18n.t('internal_server_error_heading1'),
                        locale: @locale,
                        analytics_account: settings.analytics_account,
                        user_agent: parse_user_agent }
end
