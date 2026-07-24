@smoke @auth
Feature: Login
  Authentication flow using the auth and HTTP step libraries.

  Scenario: Successful login with valid credentials
    Given the base URL is "http://localhost:8080"
    And I am not authenticated
    When I send a POST request to "/auth/login" with body
      """
      {"username": "admin", "password": "secret"}
      """
    Then the response status should be 200
    And the response JSON should contain "token"
    When I store the value "<token>" as "session_token"
    Then I should be authenticated

  Scenario: Failed login with invalid credentials
    Given the base URL is "http://localhost:8080"
    And I am not authenticated
    When I send a POST request to "/auth/login" with body
      """
      {"username": "admin", "password": "wrong"}
      """
    Then the response status should be 401
    And I should not be authenticated
