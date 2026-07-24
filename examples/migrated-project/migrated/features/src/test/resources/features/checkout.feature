Feature: Checkout

  Scenario: Complete a purchase
    Given a cart with items
    When the user checks out
    Then the order should be confirmed
