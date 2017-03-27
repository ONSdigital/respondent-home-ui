
# Class for forcing a contact name to alphanumeric characters. Non-alphanumeric
# characters are replaced with an X.
class ContactData
  def initialize(contact_data)
    @first_name = contact_data[:first_name].downcase.gsub(/[^A-Za-z0-9]/, 'X')
    @last_name  = contact_data[:last_name].downcase.gsub(/[^A-Za-z0-9]/, 'X')
  end

  def alphanumeric_name
    "#{@first_name}-#{@last_name}"
  end
end
