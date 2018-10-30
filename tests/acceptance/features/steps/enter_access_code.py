from behave import given, when, then

from tests.acceptance.features.pages import enter_access_code
from tests.config import Config
from tests.controllers import get_case


@given('a Household Respondent has received a UAC')
def respondent_navigates_to_respondent_home(_):
    enter_access_code.go_to()


@when('they enter the UAC into Respondent Home')
def respondent_enters_uac_into_respondent_home(context):
    enter_access_code.enter_uac(context.social_iac)
    enter_access_code.click_start_button()


@then('they are able to access the eQ landing page')
def respondent_is_redirected_to_eq(_):
    location = enter_access_code.get_location()
    assert Config.EQ_SURVEY_RUNNER_URL in location, location


@then('their case has transitioned to INPROGRESS')
def case_has_transitioned(context):
    case_response = get_case(context.case_id)
    case_state = case_response['caseGroup']['caseGroupStatus']
    assert case_state == 'INPROGRESS'
