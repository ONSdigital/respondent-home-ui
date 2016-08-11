
# List questionnaires for case.
get '/questionnaires/iac/:iac' do |iac|
  erb :questionnaires, locals: { iac: iac }
end
