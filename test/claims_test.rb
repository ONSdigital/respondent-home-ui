require 'test/unit'

require_relative '../lib/claims'

class ClaimsTest < Test::Unit::TestCase
  def test_english_household_questionnaire_without_sexual_identity
    claims = Claims.new(0, 'H1', nil)
    assert_equal 'household', claims.to_hash[:form_type]
    assert_equal 'GB-ENG', claims.to_hash[:region_code]
    assert_false claims.to_hash[:variant_flags][:sexual_identity]
  end

  def test_english_household_questionnaire_with_sexual_identity
    claims = Claims.new(0, 'H1S', nil)
    assert_equal 'household', claims.to_hash[:form_type]
    assert_equal 'GB-ENG', claims.to_hash[:region_code]
    assert_true claims.to_hash[:variant_flags][:sexual_identity]
  end

  def test_english_individual_questionnaire_without_sexual_identity
    claims = Claims.new(0, 'I1', nil)
    assert_equal 'individual', claims.to_hash[:form_type]
    assert_equal 'GB-ENG', claims.to_hash[:region_code]
    assert_false claims.to_hash[:variant_flags][:sexual_identity]
  end

  def test_english_individual_questionnaire_with_sexual_identity
    claims = Claims.new(0, 'I1S', nil)
    assert_equal 'individual', claims.to_hash[:form_type]
    assert_equal 'GB-ENG', claims.to_hash[:region_code]
    assert_true claims.to_hash[:variant_flags][:sexual_identity]
  end

  def test_welsh_household_questionnaire_without_sexual_identity
    claims = Claims.new(0, 'H2', nil)
    assert_equal 'household', claims.to_hash[:form_type]
    assert_equal 'GB-WLS', claims.to_hash[:region_code]
    assert_false claims.to_hash[:variant_flags][:sexual_identity]
  end

  def test_welsh_household_questionnaire_with_sexual_identity
    claims = Claims.new(0, 'H2S', nil)
    assert_equal 'household', claims.to_hash[:form_type]
    assert_equal 'GB-WLS', claims.to_hash[:region_code]
    assert_true claims.to_hash[:variant_flags][:sexual_identity]
  end

  def test_welsh_individual_questionnaire_without_sexual_identity
    claims = Claims.new(0, 'I2', nil)
    assert_equal 'individual', claims.to_hash[:form_type]
    assert_equal 'GB-WLS', claims.to_hash[:region_code]
    assert_false claims.to_hash[:variant_flags][:sexual_identity]
  end

  def test_welsh_individual_questionnaire_with_sexual_identity
    claims = Claims.new(0, 'I2S', nil)
    assert_equal 'individual', claims.to_hash[:form_type]
    assert_equal 'GB-WLS', claims.to_hash[:region_code]
    assert_true claims.to_hash[:variant_flags][:sexual_identity]
  end

  def test_hotel_questionnaire
    claims = Claims.new(0, 'HOTEL', nil)
    assert_equal 'communal-establishment', claims.to_hash[:form_type]
    assert_equal 'GB-ENG', claims.to_hash[:region_code]
    assert_false claims.to_hash[:variant_flags][:sexual_identity]
  end
end
