
# Class for forcing a contact name to alphanumeric characters. Non-alphanumeric
# characters are replaced with a dash (-).
class ContactData
  def initialize(contact_data)
    @first_name = contact_data[:first_name].gsub(/[^A-Za-z0-9]/, '?').downcase
    @last_name  = contact_data[:last_name].gsub(/[^A-Za-z0-9]/, '?').downcase
  end

  def alphanumeric_name
    "#{@first_name}-#{@last_name}"
  end
end
