error 404 do
  erb :not_found, locals: { title: I18n.t('404_not_found'),
                            host: settings.host,
                            built: @built,
                            commit: @commit,
                            environment: settings.environment,
                            analytics_account: settings.analytics_account,
                            locale: settings.locale }
end

error 429 do
  erb :too_many_requests, locals: { title: I18n.t('429_too_many_requests'),
                                    host: settings.host,
                                    built: @built,
                                    commit: @commit,
                                    environment: settings.environment,
                                    analytics_account: settings.analytics_account,
                                    locale: settings.locale }
end

error 500 do
  erb :internal_server_error, locals: { title: I18n.t('500_internal_server_error'),
                                        host: settings.host,
                                        built: @built,
                                        commit: @commit,
                                        environment: settings.environment,
                                        analytics_account: settings.analytics_account,
                                        locale: settings.locale }
end
