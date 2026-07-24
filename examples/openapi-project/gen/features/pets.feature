@api
Feature: Pets
  Scenarios for Pets generated from Petstore YAML API.

  Scenario: List all pets
    When I send a GET request to "/pets"
    Then the response status should be 200

  Scenario: Create a pet
    When I send a POST request to "/pets"
    Then the response status should be 200
