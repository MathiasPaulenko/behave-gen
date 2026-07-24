@api
Feature: Pets by petId
  Scenarios for Pets by petId generated from Petstore YAML API.

  Scenario: Info for a specific pet
    When I send a GET request to "/pets/{petId}"
    Then the response status should be 200
