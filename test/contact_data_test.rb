require 'test/unit'

require_relative '../lib/contact_data'

class ContactDataTest < Test::Unit::TestCase
  def test_alphanumeric_name_is_lowercased_and_hyphenated
    contact_data = { first_name: 'ABCDEFGHIJKLMnopqrstuvwxyz', last_name: '0123456789' }
    assert_equal 'abcdefghijklmnopqrstuvwxyz-0123456789', ContactData.new(contact_data).alphanumeric_name
  end

  def test_non_alphanumeric_name_replacement
    contact_data = { first_name: '+!"#$&\'()*+,:;=?', last_name: 'áëîòú' }
    assert_equal '????????????????-?????', ContactData.new(contact_data).alphanumeric_name
  end
end
