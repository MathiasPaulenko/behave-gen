# language: en
Feature: Login

  Scenario: Successful login
    Given a user exists
    When the user logs in with valid credentials
    Then the user should be authenticated
