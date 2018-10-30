@social
Feature: Enter UAC into RH
  As a Household Respondent
  I need to be able to enter the UAC I have been provided
  So that I can access and complete the LMS survey

  Background: The case will launch a survey and a social survey exists
  Given the case will launch a survey
  And a social survey exists

  Scenario: Respondents are able to enter a UAC into RH
    Given a Household Respondent has received a UAC
    When they enter the UAC into Respondent Home
    Then they are able to access the eQ landing page
    And their case has transitioned to INPROGRESS