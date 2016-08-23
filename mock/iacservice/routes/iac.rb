
# Gets the specified Internet Access Code and associated case details.
get '/iacs/:iac' do |iac|
  erb :case, locals: { iac: iac }
end
