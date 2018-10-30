from behave import given

from tests.controllers import (get_first_sample_summary_id, get_first_sample_unit_id_by_summary,
                               poll_for_actionable_case, poll_case_for_iacs)


@given('a social survey exists')
def create_social_survey(context):
    sample_summary_id = get_first_sample_summary_id()
    assert sample_summary_id, 'No sample summary found'

    sample_unit_id = get_first_sample_unit_id_by_summary(sample_summary_id)
    assert sample_unit_id, 'No sample unit id found'

    case = poll_for_actionable_case(sample_unit_id)
    assert case, 'No ACTIONABLE case found'
    context.case_id = case['id']

    iacs = poll_case_for_iacs(context.case_id)
    assert iacs, 'No IACs for case found'
    context.social_iac = iacs[0]['iac']


@given('the case will launch a survey')
def use_different_sample(_):
    pass
