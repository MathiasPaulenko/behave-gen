${tags}Feature: $feature_name
  CRUD scenarios for $feature_name.

  Background:
    Given a clean state for $feature_name

  Scenario Outline: create, read, update, and delete $feature_name
    When I create a $feature_name with "<value>"
    Then I can read the $feature_name with "<value>"
    When I update the $feature_name to "<new_value>"
    Then I can read the $feature_name with "<new_value>"
    When I delete the $feature_name
    Then the $feature_name no longer exists

    Examples:
      | value   | new_value  |
      | alpha   | alpha-upd  |
      | beta    | beta-upd   |
