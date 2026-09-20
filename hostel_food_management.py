"""
Hostel Food Management System

Demonstrates inheritance and polymorphism using a base class for food items.
"""

from abc import ABC, abstractmethod


class FoodItem(ABC):
    """Abstract base class for all food items."""

    def __init__(self, name: str, price: float, calories: int) -> None:
        self.name = name
        self.price = price
        self.calories = calories

    @abstractmethod
    def prepare(self) -> str:
        """Abstract method that must be implemented by concrete subclasses."""
        pass

    def __str__(self) -> str:
        return (
            f"{self.name} | Price: ${self.price:.2f} | Calories: {self.calories} kcal"
        )


class BreakfastItem(FoodItem):
    """Concrete class representing breakfast items."""

    def prepare(self) -> str:
        """Return preparation steps specific to breakfast items."""
        return (
            f"Prepare {self.name}: Sizzling omelet with toasted bread and fresh fruit. "
            "Serves 4 students."
        )


class DinnerItem(FoodItem):
    """Concrete class representing dinner items."""

    def prepare(self) -> str:
        """Return preparation steps specific to dinner items."""
        return (
            f"Prepare {self.name}: Hearty soup main course with a side salad. "
            "Serves 12 students."
        )


def demonstrate_polymorphism() -> None:
    """Create instances of different food items and call prepare() to show polymorphism."""
    breakfast = BreakfastItem(
        name="Classic Omelette Set", price=4.50, calories=320
    )
    dinner = DinnerItem(
        name="Chicken Soup Dinner", price=7.99, calories=510
    )

    food_items = [breakfast, dinner]

    for item in food_items:
        print(item)
        print(item.prepare())
        print()


if __name__ == "__main__":
    demonstrate_polymorphism()
