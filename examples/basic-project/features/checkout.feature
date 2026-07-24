@smoke @regression
Feature: Checkout
  CRUD checkout flow using the HTTP step library.

  Scenario: Create and retrieve a checkout
    Given the base URL is "http://localhost:8080"
    When I send a POST request to "/checkouts" with body
      """
      {"item": "widget", "quantity": 3}
      """
    Then the response status should be 201
    And the response JSON should contain "id"
    When I send a GET request to "/checkouts/1"
    Then the response status should be 200
    And the response JSON at "status" should be "pending"

  Scenario: Delete a checkout
    Given the base URL is "http://localhost:8080"
    When I send a DELETE request to "/checkouts/1"
    Then the response status should be 204
