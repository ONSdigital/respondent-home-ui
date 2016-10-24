
# Gets the specified Internet Access Code and associated case details.
get '/iacs/:iac' do |iac|
  erb :case_summary, locals: { iac: iac }
end
