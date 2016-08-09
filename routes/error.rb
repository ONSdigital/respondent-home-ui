error 404 do
  erb :not_found, locals: { title: '404 Not Found' }
end

error 500 do
  erb :internal_server_error, locals: { title: '500 Internal Server Error' }
end
