from tests.acceptance import browser
from tests.config import Config


def go_to():
    browser.visit(f"{Config.RESPONDENT_HOME_SERVICE}/")


def get_page_title():
    return browser.title


def click_start_button():
    browser.driver.find_element_by_class_name('qa-btn-get-started').click()


def enter_uac(uac):
    iac1, iac2, iac3 = uac[:4], uac[4:8], uac[8:]
    browser.driver.find_element_by_id('iac1').send_keys(iac1)
    browser.driver.find_element_by_id('iac2').send_keys(iac2)
    browser.driver.find_element_by_id('iac3').send_keys(iac3)


def get_location():
    return browser.url
