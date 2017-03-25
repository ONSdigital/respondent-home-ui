require 'i18n'

# Class for forcing a contact name to ASCII, ignoring spaces and multiple first
# and last names.
class ContactData
  def initialize(contact_data)
    I18n.available_locales = [:en]
    I18n.default_locale = :en
    I18n.locale = :en
    @first_first_name = contact_data[:first_name].strip.split(/\s+/).first.downcase
    @first_last_name  = contact_data[:last_name].strip.split(/\s+/).first.downcase
  end

  def ascii_name
    I18n.transliterate("#{@first_first_name}-#{@first_last_name}")
  end
end
