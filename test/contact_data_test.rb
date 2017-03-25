require 'test/unit'

require_relative '../lib/contact_data'

class ContactDataTest < Test::Unit::TestCase
  def test_ascii_single_first_and_single_last_names
    contact_data = { first_name: 'First', last_name: 'Last' }
    assert_equal 'first-last', ContactData.new(contact_data).ascii_name
  end

  def test_ascii_single_first_and_multiple_last_names
    contact_data = { first_name: 'First', last_name: 'Last Second' }
    assert_equal 'first-last', ContactData.new(contact_data).ascii_name
  end

  def test_ascii_multiple_first_and_single_last_names
    contact_data = { first_name: 'First Second', last_name: 'Last' }
    assert_equal 'first-last', ContactData.new(contact_data).ascii_name
  end

  def test_ascii_multiple_first_and_multiple_last_names
    contact_data = { first_name: 'First Second', last_name: 'Last Second' }
    assert_equal 'first-last', ContactData.new(contact_data).ascii_name
  end

  def test_ascii_single_first_and_single_last_names_with_spaces
    contact_data = { first_name: ' First  ', last_name: '  Last ' }
    assert_equal 'first-last', ContactData.new(contact_data).ascii_name
  end

  def test_ascii_multiple_first_and_multiple_last_names_with_spaces
    contact_data = { first_name: ' First   Second ', last_name: '  Last   Second ' }
    assert_equal 'first-last', ContactData.new(contact_data).ascii_name
  end

  def test_unicode_single_first_and_single_last_names
    contact_data = { first_name: 'Fîrst', last_name: 'Lást' }
    assert_equal 'first-last', ContactData.new(contact_data).ascii_name
  end

  def test_unicode_single_first_and_multiple_last_names
    contact_data = { first_name: 'Fîrst', last_name: 'Lást Secönd' }
    assert_equal 'first-last', ContactData.new(contact_data).ascii_name
  end

  def test_unicode_multiple_first_and_single_last_names
    contact_data = { first_name: 'Fîrst Second', last_name: 'Lást' }
    assert_equal 'first-last', ContactData.new(contact_data).ascii_name
  end

  def test_unicode_multiple_first_and_multiple_last_names
    contact_data = { first_name: 'Fîrst Secönd', last_name: 'Lást Secönd' }
    assert_equal 'first-last', ContactData.new(contact_data).ascii_name
  end

  def test_unicode_single_first_and_single_last_names_with_spaces
    contact_data = { first_name: ' Fîrst  ', last_name: '  Lást ' }
    assert_equal 'first-last', ContactData.new(contact_data).ascii_name
  end

  def test_unicode_multiple_first_and_multiple_last_names_with_spaces
    contact_data = { first_name: ' Fîrst   Secönd ', last_name: '  Lást   Secönd ' }
    assert_equal 'first-last', ContactData.new(contact_data).ascii_name
  end
end
