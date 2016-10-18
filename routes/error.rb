error 404 do
  erb :not_found, locals: { title: I18n.t('404_not_found') }
end

error 500 do
  erb :internal_server_error, locals: { title: I18n.t('500_internal_server_error') }
end
