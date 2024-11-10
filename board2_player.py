import numpy as np
import os
import time
import shutil
import traceback

Ship_Classes = {'Carrier': 5, 'Battleship': 4, 'Cruiser': 3, 'Submarine': 3, 'Destroyer': 2}
Ship_Letters = {'Carrier': 'C', 'Battleship': 'B', 'Cruiser': 'R', 'Submarine': 'S', 'Destroyer': 'D'}

class Board:

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid = np.zeros((height, width), dtype=str)
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

            # Vertical or horizontal placements
            vert_or_horizontal = np.random.choice([0, 1])

            if vert_or_horizontal == 1:  # Vertical placements
                if self.is_valid_placement(row, col, length, True):
                    for i in range(length):
                        self.grid[row + i, col] = ship_letter
                        self.ship_positions[ship_name].append((row + i, col))
                    placed_ships += 1
            else:  # Horizontal placement
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

        try:
            row, col = self.convert_input(target)
            if row < 0 or col < 0:
                raise ValueError

            if (row, col) in self.hits or (row, col) in self.misses:
                return False, "Already targeted this position!"

            if self.board.grid[row, col] != ' ' and self.board.grid[row, col] not in ['X', 'O']:  # Hit
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

def display_side_by_side(board1: Board, board2: Board, player_names, current_player_index):
    """Display boards side by side with boards in fixed positions"""
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    # Getting terminal size
    terminal_size = shutil.get_terminal_size((80, 20))
    terminal_width = terminal_size.columns

    # Prepare content
    board_width = 5 * (board1.width + board2.width + 5)  # Approximate width of both boards with padding
    side_padding = max((terminal_width - board_width) // 2, 0)  # Calculate left/right padding

    print(" " * side_padding + " "*(3*board1.width//2 + 1) + f"{player_names[0]}'s BOARD" + " " * ((3*board1.width//2 + 12) + (3* board2.width//2 -4))  + f"{player_names[1]}'s BOARD")
    print(" " * side_padding + "    " + " ".join(f"{i + 1:^3}" for i in range(board1.width)) + " " * 10 + "     " + " ".join(f"{i + 1:^3}" for i in range(board2.width)))
    print(" " * side_padding + "   +" + "---+" * board1.width + " " * 10 + "   +" + "---+" * board2.width)

    for row_num in range(board1.height):
        # Hide ships accordingly
        if current_player_index == -1:
            # Game over: reveal all ships
            board1_row = board1.grid[row_num]
            board2_row = board2.grid[row_num]
        else:
            # During the game: hide ships on both boards
            board1_row = [cell if cell in ['X', 'O'] else ' ' for cell in board1.grid[row_num]]
            board2_row = [cell if cell in ['X', 'O'] else ' ' for cell in board2.grid[row_num]]

        board1_row_content = "|".join(f"{str(cell):^3}" for cell in board1_row)
        board2_row_content = "|".join(f"{str(cell):^3}" for cell in board2_row)

        # Print content with padding
        print(f"{' ' * side_padding}{alphabet[row_num]:^2} |{board1_row_content}| {' ' * 10}{alphabet[row_num]:^2}|{board2_row_content}|")
        print(" " * side_padding + "   +" + "---+" * board1.width + " " * 10 + "   +" + "---+" * board2.width)


def format_time(seconds):
    """HH:MM:SS"""
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

def game_loop(player1_board, player2_board, player1_targeting, player2_targeting, player_names):
    """Main game loop for two players"""

    elapsed_time = {player_names[0]: 0, player_names[1]: 0}
    start_time = time.time()
    messages = {player_names[0]: [], player_names[1]: []}  # Messages for each player
    tries = {player_names[0]: 0, player_names[1]: 0}  # Number of tries for each player

    current_player = 0  # Index to switch between players
    winner = None
    loser = None

    while True:
        try:
            # Determine current and opponent players
            player = player_names[current_player]
            opponent = player_names[1 - current_player]
            player_board = [player1_board, player2_board][current_player]
            opponent_board = [player1_board, player2_board][1 - current_player]
            player_targeting = [player1_targeting, player2_targeting][current_player]
            opponent_targeting = [player1_targeting, player2_targeting][1 - current_player]

            # Clear terminal and display boards
            Board.clear_terminal()
            print(f"{player}'s Turn")
            display_side_by_side(player1_board, player2_board, player_names, current_player)
            print(f"Shots fired : {tries[player]}")
            ms1 = f"{player}'s Shot History"
            print("="*len(ms1))
            print(ms1)
            print("="*len(ms1))
            

            # Print last messages
            for msg in messages[player][-2:]:
                print(msg)

            # Input validation loop
            while True:
                user_input = input(f"\n{player}, enter target (e.g., A1) or type 'q' to quit: ").strip().upper()

                if user_input == 'Q':
                    elapsed_time[player] += time.time() - start_time
                    Board.clear_terminal()
                    print(f"Shots Fired : {tries[player]}")
                    print(format_time(elapsed_time[player]))
                    print(f"\nGame ended early by {player}.")
                    return

                elif len(user_input) >= 2:
                    row_char = user_input[0]
                    col_str = user_input[1:]

                    if row_char.isalpha() and col_str.isdigit():
                        row_index = ord(row_char.upper()) - ord('A')
                        col_index = int(col_str) - 1
                        if 0 <= row_index < player_board.height and 0 <= col_index < player_board.width:
                            break  # Valid input
                print("Invalid input. Please enter a valid coordinate (e.g., A1, B3).")

            # Fire
            success, message = player_targeting.fire(user_input)
            if message:
                messages[player].append(message)

            if not success:
                # If the shot was invalid (e.g., already targeted), re-prompt without proceeding
                continue  # Go back to the beginning of the loop to redraw the board and re-prompt

            tries[player] += 1  # Increment player's tries

            # Check if player has won
            if player_targeting.game_over:
                winner = player
                loser = opponent
                elapsed_time[player] += time.time() - start_time
                break

            # Switch turns
            current_player = 1 - current_player

        except Exception as e:
            print(f"An error occurred: {e}")
            tb = traceback.extract_tb(e.__traceback__)
            print("Custom formatted traceback:")
            for frame in tb:
                print(f"File: {frame.filename}, Line: {frame.lineno}, Function: {frame.name}")
            break  # End the game due to an error

    # Game ended, display summary
    Board.clear_terminal()
    # Show both boards with all ships revealed
    display_side_by_side(player1_board, player2_board, player_names, current_player_index=-1)
    total_time = time.time() - start_time
    print(f"\nTotal Game Time: {format_time(total_time)}")
    print(f"{player_names[0]}'s Number of Shots: {tries[player_names[0]]}")
    print(f"{player_names[1]}'s Number of Shots: {tries[player_names[1]]}")

    if winner:
        print(f"\nGame Over! {winner} has sunk all {loser}'s ships!")
    else:
        print("\nGame Over!")

    return [winner, loser, format_time(total_time), tries[winner]]

def game_loop_setup():
    # Initialize players
    player_names = []
    print("Welcome to Battleship Game for Two Players!")
    player_names.append(input("Enter name for Player 1: ").strip() or "Player 1")
    player_names.append(input("Enter name for Player 2: ").strip() or "Player 2")

    # Create boards for both players
    player1_board = Board(5, 5)  # Player 1's board
    player1_board.place_ships_random()

    player2_board = Board(5, 5)  # Player 2's board
    player2_board.place_ships_random()

    # Create targeting systems
    player1_targeting = TargetingSystem(player2_board)
    player2_targeting = TargetingSystem(player1_board)

    # Start the game loop
    return game_loop(player1_board, player2_board, player1_targeting, player2_targeting, player_names)


if __name__ == "__main__":
    print(game_loop_setup())