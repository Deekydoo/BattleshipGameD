import numpy as np
import os
import random
import shutil
import time
import traceback

Ship_Classes = {'Carrier':5, 'Battleship':4,'Cruiser':3,'Submarine':3, 'Destroyer':2}
Ship_Letters = {'Carrier':'C', 'Battleship':'B','Cruiser':'R','Submarine':'S', 'Destroyer':'D'}

class Board:

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid = np.zeros((width, height), dtype=str)
        self.grid[:] = ' '
        self.ship_positions = {ship: [] for ship in Ship_Classes}
        self.ships_sunk = 0

    @staticmethod
    def clear_terminal():
        os.system('cls' if os.name == 'nt' else 'clear')

    def is_valid_placement(self, row, col, length, vertical):

        if vertical:
            if row + length > self.height:
                return False  # Ship would go out of bounds
            for i in range(length):
                if self.grid[row + i, col] != ' ':
                    return False  # Ship would overlap

        else:
            if col + length > self.width:
                return False  # Ship would go out of bounds
            for i in range(length):
                if self.grid[row, col + i] != ' ':
                    return False  # Ship would overlap

        return True

    def place_ships_random(self, num_ships=len(Ship_Classes)):
        placed_ships = 0
        ship_list = list(Ship_Classes.items())

        while placed_ships < num_ships:
            ship_name, length = ship_list[placed_ships]
            ship_letter = Ship_Letters[ship_name]

            row = np.random.randint(0, self.height)
            col = np.random.randint(0, self.width)

            # Vertical or horizontal
            vert_or_horizontal = np.random.choice([0, 1])

            if vert_or_horizontal == 1:  # Vertical Placements
                if self.is_valid_placement(row, col, length, True):
                    for i in range(length):
                        self.grid[row + i, col] = ship_letter
                        self.ship_positions[ship_name].append((row + i, col))
                    placed_ships += 1
            else:  # Horizontal Placement
                if self.is_valid_placement(row, col, length, False):
                    for i in range(length):
                        self.grid[row, col + i] = ship_letter
                        self.ship_positions[ship_name].append((row, col + i))
                    placed_ships += 1

class TargetingSystem:

    def __init__(self, board: Board):
        self.board = board
        self.hits = set()  # Keep track of hit positions
        self.misses = set()  # Keep track of miss positions
        self.game_over = False  # Track if the game is over

    def convert_input(self, target: str):
        # Converting target like 'A1' to row and column indices
        letter_to_row = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        row = letter_to_row.index(target[0].upper())  # Convert letter to row index
        col = int(target[1:]) - 1
        return row, col

    def fire(self, target: str):
        # Fire at a coordinate given as 'A1', 'B2', etc
        letter_to_row = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

        if self.game_over:
            return False, "Game over! All ships have been sunk."

        row, col = self.convert_input(target)
        try:
            if row < 0 or col < 0:
                raise ValueError

            if (row, col) in self.hits or (row, col) in self.misses:
                return False, "Already targeted this position!"

            if self.board.grid[row, col] != ' ':  # Hit
                ship_letter = self.board.grid[row, col]
                self.hits.add((row, col))
                self.board.grid[row, col] = 'X'
                ship_name = [key for key, value in Ship_Letters.items() if value == ship_letter][0]
                message = (f"\n <<< SHIP HIT! >>>\nYou hit opponent's {ship_name} at {letter_to_row[row]}{col + 1}.")
                self.check_if_ship_sunk(ship_letter)
                return True, message
            else:  # Miss
                self.misses.add((row, col))
                self.board.grid[row, col] = 'O'
                message = (f"\n <<< MISS! >>>\nNo ship at {target}.")
                return True, message

        except Exception as e:
            return False, f"You can't shoot there. {e}"

    def check_if_ship_sunk(self, ship_letter):
        # Check if ship has been fully sunk
        for ship_name, positions in self.board.ship_positions.items():
            if Ship_Letters[ship_name] == ship_letter:
                # Check if all positions have been hit
                if all(self.board.grid[row, col] == 'X' for row, col in positions):
                    print(f"You have sunk opponent's {ship_name}!")
                    self.board.ships_sunk += 1
                    self.check_if_all_ships_sunk()
                return

    def check_if_all_ships_sunk(self):
        # Check if all ships have been sunk and end the game
        if self.board.ships_sunk == len(Ship_Classes):
            self.game_over = True
            return "All ships have been sunk! You win!"

class PseudoAI:
    def __init__(self, board: Board, opponent_board: Board):
        self.board = board
        self.opponent_board = opponent_board
        self.hits = set()
        self.misses = set()
        self.tries = 0
        self.remaining_targets = set((row, col) for row in range(self.opponent_board.height) for col in range(self.opponent_board.width))
        self.game_over = False

    def random_fire(self):
        """Randomly picks a coordinate to fire without repeating"""
        letter_to_row = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

        if not self.remaining_targets:
            return "No remaining targets for AI to fire at."

        row, col = random.choice(list(self.remaining_targets))
        self.remaining_targets.remove((row, col))

        if self.opponent_board.grid[row, col] != ' ' and self.opponent_board.grid[row, col] != 'X' and self.opponent_board.grid[row, col] != 'O':
            # Hit
            ship_letter = self.opponent_board.grid[row, col]
            self.hits.add((row, col))
            self.opponent_board.grid[row, col] = 'X'
            ship_name = [key for key, value in Ship_Letters.items() if value == ship_letter][0]
            message = (f"\n <<< SHIP HIT! >>>\nAI hits your {ship_name} at {letter_to_row[row]}{col + 1}.")
            self.check_if_ship_sunk(ship_letter)  # Check if the ship is sunk
        else:
            # Miss
            self.misses.add((row, col))
            self.opponent_board.grid[row, col] = 'O'
            message = (f"\n <<< MISS! >>>\nAI misses at {letter_to_row[row]}{col + 1}.")

        self.tries += 1  # Increment AI's tries
        return message

    def check_if_ship_sunk(self, ship_letter):
        # Check if ship has been fully sunk
        for ship_name, positions in self.opponent_board.ship_positions.items():
            if Ship_Letters[ship_name] == ship_letter:
                # Check if all positions have been hit
                if all(self.opponent_board.grid[row, col] == 'X' for row, col in positions):
                    print(f"AI has sunk your {ship_name}!")
                    self.opponent_board.ships_sunk += 1
                    self.check_if_all_ships_sunk()
                return

    def check_if_all_ships_sunk(self):
        # Check if all player's ships have been sunk
        if self.opponent_board.ships_sunk == len(Ship_Classes):
            self.game_over = True

def display_side_by_side(user_board: Board, ai_board: Board, hide_ships=False):
    """Display boards side by side"""
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    # Getting terminal size
    terminal_size = shutil.get_terminal_size((80, 20))
    terminal_width = terminal_size.columns

    # Prepare content
    board_width = 5 * (user_board.width + ai_board.width + 5)  # Approximate width of both boards with padding
    side_padding = max((terminal_width - board_width) // 2, 0)  # Calculate left/right padding

    print(" " * side_padding + " "*(3*user_board.width//2 + 1) +"YOUR BOARD"+ " " * ((3*user_board.width//2 + 12) + (3* ai_board.width//2 -4))  + "OPPONENT'S BOARD")
    print(" " * side_padding + "    " + " ".join(f"{i + 1:^3}" for i in range(user_board.height)) + " " * 10 + "     " + " ".join(f"{i + 1:^3}" for i in range(ai_board.height)))
    print(" " * side_padding + "   +" + "---+" * user_board.width + " " * 10 + "   +" + "---+" * ai_board.width)

    for row_num in range(user_board.height):
        user_row_content = "|".join(f"{str(cell):^3}" for cell in user_board.grid[row_num])
        ai_row_content = "|".join(f"{str(cell):^3}" for cell in ai_board.grid[row_num])

        # Hiding ships
        if hide_ships:
            user_row_content = "|".join(f"{str(cell) if cell in ['X', 'O'] else ' ':^3}" for cell in user_board.grid[row_num])
            ai_row_content = "|".join(f"{str(cell) if cell in ['X', 'O'] else ' ':^3}" for cell in ai_board.grid[row_num])

        # Print content with padding
        print(f"{' ' * side_padding}{alphabet[row_num]:^2} |{user_row_content}| {' ' * 10}{alphabet[row_num]:^2}|{ai_row_content}|")
        print(" " * side_padding + "   +" + "---+" * user_board.width + " " * 10 + "   +" + "---+" * ai_board.width)

def format_time(seconds):
    """HH:MM:SS"""

    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

def game_loop(user_board, ai_board, targeting_system, ai):
    """Main game loop"""

    user_input = ' '
    elapsed_time = 0
    end_early = False
    start_time = time.time()
    messages = []  # List to store messages
    player_tries = 0  # Initialize player's number of tries
    winner = None
    loser = None

    while True:
        try:
            Board.clear_terminal()
            display_side_by_side(user_board, ai_board, hide_ships=True)
            print(f"Shot Count : {player_tries}")
            # Print the last few messages
            for msg in messages[-2:]:
                print(msg)

            # Input validation loop
            while True:
                user_input = input("\nEnter target (e.g., A1) or type 'q' to quit: ").strip().upper()

                if user_input == 'Q':
                    end_early = True
                    end_time = time.time()
                    elapsed_time = end_time - start_time
                    Board.clear_terminal()
                    print(f"Try Count : {player_tries}")
                    print(format_time(elapsed_time))
                    break  # Break out of the validation loop and end the game

                elif len(user_input) == 2:
                    row_char = user_input[0]
                    col_char = user_input[1]

                    if row_char.isalpha():
                        row_index = ord(row_char) - ord('A')
                        if 0 <= row_index < user_board.height:
                            if col_char.isdigit():
                                col_index = int(col_char) - 1
                                if 0 <= col_index < user_board.width:
                                    break  # Valid input
                    print("Invalid input. Please enter a valid coordinate (e.g., A1, B3).")
                else:
                    print("Invalid input. Please enter a valid coordinate (e.g., A1, B3) or 'q' to quit.")

            if end_early:
                break  # Break out of the main loop and end the game

            # Fire
            success, message = targeting_system.fire(user_input)
            if message:
                messages.append(message)

            if not success:
                # If the shot was invalid (e.g., already targeted), re-prompt without proceeding
                continue  # Go back to the beginning of the loop to redraw the board and re-prompt

            player_tries += 1  # Increment player's tries

            # Check if player has won
            if targeting_system.game_over:
                winner = 'Player'
                loser = 'AI'
                elapsed_time = time.time() - start_time
                break

            # AI takes a shot
            ai_message = ai.random_fire()
            if ai_message:
                messages.append(ai_message)

            # Check if AI has won
            if ai.game_over:
                winner = 'AI'
                loser = 'Player'
                elapsed_time = time.time() - start_time
                break



        except Exception as e:
            print(f"An error occurred: {e}")
            elapsed_time = time.time() - start_time
            tb = traceback.extract_tb(e.__traceback__)
            print("Custom formatted traceback:")
            for frame in tb:
                print(f"File: {frame.filename}, Line: {frame.lineno}, Function: {frame.name}")
            break  # End the game due to an error

    # Game ended, display summary
    Board.clear_terminal()
    display_side_by_side(user_board, ai_board, hide_ships=False)
    print(f"\nTime Elapsed: {format_time(elapsed_time)}")
    print(f"Player's Number of Shots: {player_tries}")
    print(f"AI's Number of Shots: {ai.tries}")

    if end_early:
        print("\nGame ended early by the player.")
    elif winner:
        print(f"\nGame Over! {winner} has sunk all {loser}'s ships!")
    else:
        print("\nGame Over!")

    return [winner, loser, format_time(elapsed_time), player_tries]

if __name__ == "__main__":
    user_board = Board(5, 5)  # User's board
    user_board.place_ships_random()

    ai_board = Board(5, 5)  # AI's board
    ai_board.place_ships_random()

    # Create targeting system
    targeting_system = TargetingSystem(ai_board)

    # Create AI
    ai = PseudoAI(ai_board, user_board)

    print(game_loop(user_board, ai_board, targeting_system, ai))
