import random


class SnakeAndLadder:
    def __init__(self):
        self.board_size = 100
        # Standard ladder positions (base: top)
        self.ladders = {
            1: 38,
            4: 14,
            9: 31,
            21: 42,
            28: 84,
            36: 44,
            51: 67,
            71: 91,
            80: 100,
        }
        # Standard snake positions (head: tail)
        self.snakes = {
            100: 1,
            99: 78,
            96: 75,
            95: 74,
            92: 88,
            89: 53,
            70: 3,
            69: 33,
            68: 32,
            62: 19,
            55: 5,
            52: 26,
            48: 9,
            47: 25,
            43: 17,
            37: 20,
            34: 6,
            17: 7,
        }
        self.current_position = 1

    def roll_die(self):
        """Generate a random integer between 1 and 6 to simulate rolling a die."""
        return random.randint(1, 6)

    def move(self, steps):
        """
        Move the player forward by the given number of steps.
        If the target exceeds 100, the player stays at the previous position.
        If landing on a ladder base, move to the top.
        If landing on a snake head, slide to the tail.
        """
        target = self.current_position + steps

        if target > self.board_size:
            return self.current_position

        # Check for ladder
        if target in self.ladders:
            self.current_position = self.ladders[target]
        # Check for snake
        elif target in self.snakes:
            self.current_position = self.snakes[target]
        # Normal move
        else:
            self.current_position = target

        return self.current_position

    def check_win(self):
        """Check if the player has reached square 100."""
        return self.current_position == self.board_size


def main():
    game = SnakeAndLadder()
    print("Welcome to Snake and Ladder!")
    print(f"Starting position: {game.current_position}")

    while not game.check_win():
        # Prompt user to roll
        input("Press Enter to roll the die...")
        roll = game.roll_die()
        print(f"You rolled {roll}! Moving...")

        old_pos = game.current_position
        new_pos = game.move(roll)

        if new_pos != old_pos + roll and new_pos == old_pos + roll:
            pass # Normal move, no special message needed unless we want to simplify

        if new_pos != old_pos + roll:
             # It could be a snake or ladder
             if old_pos + roll in game.ladders:
                 print(f"Landed on a ladder! Moving up to {new_pos}")
             elif old_pos + roll in game.snakes:
                 print(f"Landed on a snake! Sliding down to {new_pos}")
             else:
                 # If it stayed same due to >100
                 if old_pos + roll > 100:
                     print(f"Cannot move past 100. Staying at {old_pos}")
        else:
             print(f"Moving to {new_pos}")

        if game.check_win():
            print("Congratulations! You have won the game!")
            break


if __name__ == "__main__":
    main()
