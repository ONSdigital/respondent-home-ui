require 'securerandom'

# Class to generate a hash of claims from a case reference, question set and
# language code.
class Claims
  attr_reader :transaction_id

  def initialize(case_reference, question_set, language_code)
    @case_reference  = case_reference.to_s
    @question_set    = question_set.downcase
    @language_code   = language_code
    @region_code     = @question_set.include?('2') ? 'GB-WLS' : 'GB-ENG'
    @sexual_identity = @question_set.end_with?('s')
    @transaction_id  = SecureRandom.uuid

    if @question_set == 'hotel'
      @form_type = 'communal'
    else
      @form_type = 'household'  if @question_set.start_with?('h')
      @form_type = 'individual' if @question_set.start_with?('i')
    end
  end

  def to_hash
    {
      collection_exercise_sid: '0',
      eq_id: 'census',
      exp: Time.now.to_i + 60 * 60,
      form_type: @form_type,
      iat: Time.now.to_i,
      language_code: @language_code,
      period_id: '',
      period_str: '',
      ref_p_start_date: '2000-01-01',
      ref_p_end_date: '2000-01-01',
      region_code: @region_code,
      ru_name: '',
      ru_ref: @case_reference,
      return_by: '2000-01-01',
      tx_id: @transaction_id,
      user_id: '',
      variant_flags: {
        sexual_identity: @sexual_identity
      }
    }
  end

  def to_s
    "form_type=#{@form_type}, language_code=#{@language_code}, region_code=#{@region_code}, si=#{@sexual_identity}, tx_id=#{@transaction_id}"
  end
end
