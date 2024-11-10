# For game Classes
from board import Board, TargetingSystem, game_loop, PseudoAI

# For 2 player
from board2_player import game_loop_setup

# For History
from history import print_read_file
from datetime import datetime

# For Leaderboard
from leaderboard import leaderboard_main

# For UI
import os
import sys
import termios
import tty
import shutil
import functools
import logging

# Configure logging
logging.basicConfig(
    filename='game.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Decorators
def confirm_quit(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if result == "Exit":
            confirmation = input("Are you sure you want to quit? (y/n): ").lower()
            if confirmation == 'y':
                return "Exit"
            else:
                return None
        return result
    return wrapper

def require_confirmation(func):  # Not currently used
    """Decorator to require user confirmation before executing a function."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        confirmation = input(f"Do you want to proceed with '{func.__name__}'? (y/n): ").lower()
        if confirmation == 'y':
            return func(*args, **kwargs)
        else:
            print("Action canceled.")
            logging.info(f"Action '{func.__name__}' canceled by user.")
    return wrapper

# cool asf
def log_function_call(func):  # Not currently used
    """Decorator to log function calls with arguments and return values."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logging.info(f"Called {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logging.info(f"{func.__name__} returned {result}")
            return result
        except Exception as e:
            logging.error(f"Error in {func.__name__}: {e}")
            raise
    return wrapper

# Whatever errors may be
def handle_errors(func):
    """Decorator to handle exceptions and provide user-friendly messages."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as ve:
            print(f"Value Error in {func.__name__}: {ve}")
            logging.error(f"Value Error in {func.__name__}: {ve}")
        except Exception as e:
            print(f"An unexpected error occurred in {func.__name__}: {e}")
            logging.error(f"Unexpected Error in {func.__name__}: {e}")
    return wrapper

# MenuSystem Base Class
class MenuSystem:

    def __init__(self, options):
        self.options = options
        self.selected_index = 0
        self.in_menu = "Main"

    def get_key(self):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == '\x1b':
                ch += sys.stdin.read(2)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        return ch

    @staticmethod
    def clear_terminal():
        os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def get_terminal_size():
        size = shutil.get_terminal_size(fallback=(80, 20))
        return size

    @staticmethod
    def center_text(text, width):
        return text.center(width)

    def display_menu(self):

        self.clear_terminal()

        self.width, self.height = self.get_terminal_size()

        terminal_width = self.width
        terminal_height = self.height

        max_len = max(len(option) for option in self.options)
        box_width = max_len + 6  # Add padding for the box around the text

        if self.in_menu == "Main":
            title = "Welcome to Battleship"
        elif self.in_menu == "SubMenu":
            title = "Mode Selection"
        elif self.in_menu == "Singleplayer":
            title = "Difficulty"
        elif self.in_menu == "SubMenu_Hist":
            title = "Game History"
        elif self.in_menu == "SubMenu_Lead":
            title = "Game Leaderboards"
        else:
            title = "Null"

        print(self.center_text(title, terminal_width))
        print(self.center_text("=" * (len(title) + 2), terminal_width))

        # Top of the box
        print(self.center_text("+" + "-" * box_width + "+", terminal_width))

        for i, option in enumerate(self.options):
            if i == self.selected_index:
                option_str = f"> {option} <".center(box_width)
            else:
                option_str = f" {option} ".center(box_width)

            print(self.center_text(f"|{option_str}|", terminal_width))

        print(self.center_text("+" + "-" * box_width + "+", terminal_width))

    @confirm_quit
    def navigate(self):
        while True:
            self.display_menu()
            key = self.get_key()

            if key == '\x1b[A':
                self.selected_index = (self.selected_index - 1) % len(self.options)
            elif key == '\x1b[B':
                self.selected_index = (self.selected_index + 1) % len(self.options)
            elif key == '\n' or key == '\r':
                return self.options[self.selected_index]
            elif key == 'q':
                return "Exit"

# MainMenu Class with Dictionary Comprehension and Signal Handling
class MainMenu(MenuSystem):

    def __init__(self):
        super().__init__(["Play", "History", "Leaderboard", "Exit"])
        self.in_menu = "Main"
        # Initialize the option_handlers dictionary
        self.option_handlers = {option: getattr(self, f"handle_{option.lower()}") for option in self.options}

    @log_function_call
    @handle_errors
    def handle_selection(self):
        while True:
            selected_option = self.navigate()

            # Check for the "Exit" signal first
            if selected_option == "Exit":
                self.clear_terminal()
                sys.exit()

            handler = self.option_handlers.get(selected_option)
            if handler:
                result = handler()
                if result == "Exit":
                    self.clear_terminal()
                    sys.exit()
                elif result == "Back":
                    break  # Not applicable here, but included for consistency
            else:
                print("Invalid option selected.")
                logging.warning(f"Invalid main menu option selected: {selected_option}")

    def handle_play(self):
        submenu = SubMenu("Mode Selection", ["Singleplayer", "Multiplayer", "Back"])
        return submenu.handle_selection()

    def handle_history(self):
        submenu_hist = SubMenu_History("Game History", ["Easy Games", "Medium Games", "Hard Games", "Back"])
        return submenu_hist.handle_selection()

    def handle_leaderboard(self):
        submenu_lead = SubMenu_Leaderboard("Game Leaderboards", ["Easy Leaderboard", "Medium Leaderboard", "Hard Leaderboard", "Back"])
        return submenu_lead.handle_selection()

    def handle_exit(self):
        return "Exit"

# SubMenu_History Class with Dictionary Comprehension and Signal Handling
class SubMenu_History(MenuSystem):
    def __init__(self, title, options):
        super().__init__(options)
        self.title = title
        self.in_menu = "SubMenu_Hist"
        self.option_handlers = {option: getattr(self, f"handle_{option.lower().replace(' ', '_')}") for option in self.options}

    @log_function_call
    @handle_errors
    def handle_selection(self):
        while True:
            selected_option = self.navigate()

            # Check for the "Exit" signal first
            if selected_option == "Exit":
                self.clear_terminal()
                sys.exit()

            handler = self.option_handlers.get(selected_option)
            if handler:
                result = handler()
                if result == "Back":
                    break
                elif result == "Exit":
                    self.clear_terminal()
                    sys.exit()
            else:
                print("Invalid option selected.")
                logging.warning(f"Invalid history menu option selected: {selected_option}")

    def handle_easy_games(self):
        self.display_game_history('txt_files/easy_game_history.txt')
        return

    def handle_medium_games(self):
        self.display_game_history('txt_files/medium_game_history.txt')
        return

    def handle_hard_games(self):
        self.display_game_history('txt_files/hard_game_history.txt')
        return

    def handle_back(self):
        return "Back"

    def display_game_history(self, file_path):
        self.clear_terminal()
        message = f"LIST OF {file_path.split('_')[1].upper()} GAMES PLAYED"
        print(message)
        print("=" * len(message))
        print("Format = Player Name, date-time, Winner, Loser, Game time, Game Turns")
        print("=" * len(message))
        print_read_file(file_path)
        input("\nPress Enter to continue...")
        return

# SubMenu_Leaderboard Class with Dictionary Comprehension and Signal Handling
class SubMenu_Leaderboard(MenuSystem):
    def __init__(self, title, options):
        super().__init__(options)
        self.title = title
        self.in_menu = "SubMenu_Lead"
        self.option_handlers = {option: getattr(self, f"handle_{option.lower().replace(' ', '_')}") for option in self.options}

    @log_function_call
    @handle_errors
    def handle_selection(self):
        while True:
            selected_option = self.navigate()

            # Check for the "Exit" signal first
            if selected_option == "Exit":
                self.clear_terminal()
                sys.exit()

            handler = self.option_handlers.get(selected_option)
            if handler:
                result = handler()
                if result == "Back":
                    break
                elif result == "Exit":
                    self.clear_terminal()
                    sys.exit()
            else:
                print("Invalid option selected.")
                logging.warning(f"Invalid leaderboard menu option selected: {selected_option}")

    def handle_easy_leaderboard(self):
        self.display_leaderboard('txt_files/easy_game_history.txt', "EASY GAME LEADERBOARD")
        return

    def handle_medium_leaderboard(self):
        self.display_leaderboard('txt_files/medium_game_history.txt', "MEDIUM GAME LEADERBOARD")
        return

    def handle_hard_leaderboard(self):
        self.display_leaderboard('txt_files/hard_game_history.txt', "HARD GAME LEADERBOARD")
        return

    def handle_back(self):
        return "Back"

    def display_leaderboard(self, file_path, title):
        self.clear_terminal()
        print(title)
        print("=" * len(title))
        print("Format = Player Name, date-time, Winner, Loser, Game time, Game Turns")
        print("=" * len(title))
        leaderboard_main(file_path)
        input("\nPress Enter to go back.")
        return

# SubMenu Class with Dictionary Comprehension and Signal Handling
class SubMenu(MenuSystem):
    def __init__(self, title, options):
        super().__init__(options)
        self.title = title
        self.in_menu = "SubMenu"
        self.option_handlers = {option: getattr(self, f"handle_{option.lower()}") for option in self.options}

    @log_function_call
    @handle_errors
    def handle_selection(self):
        while True:
            selected_option = self.navigate()

            # Check for the "Exit" signal first
            if selected_option == "Exit":
                self.clear_terminal()
                sys.exit()

            handler = self.option_handlers.get(selected_option)
            if handler:
                result = handler()
                if result == "Back":
                    break
                elif result == "Exit":
                    self.clear_terminal()
                    sys.exit()
            else:
                print("Invalid option selected.")
                logging.warning(f"Invalid submenu option selected: {selected_option}")

    def handle_singleplayer(self):
        singeplayermenu = SingleplayerMenu("Difficulty Selection", ["Easy", "Medium", "Hard", "Back"])
        return singeplayermenu.handle_selection()

    def handle_multiplayer(self):
        self.clear_terminal()
        game_loop_setup()
        input("Press Enter to continue...")
        return

    def handle_back(self):
        return "Back"

# SingleplayerMenu Class with Dictionary Comprehension and Signal Handling
class SingleplayerMenu(MenuSystem):
    def __init__(self, title, options):
        super().__init__(options)
        self.title = title
        self.in_menu = "Singleplayer"
        self.option_handlers = {option: getattr(self, f"handle_{self.format_option(option)}") for option in self.options}
        self.player_stats = {}

    def format_option(self, option):
        """
        Converts option strings to method-friendly format.
        E.g., "Easy" -> "easy"
        """
        return option.lower()

    @log_function_call
    @handle_errors
    def handle_selection(self):
        while True:
            selected_option = self.navigate()

            # Check for the "Exit" signal first
            if selected_option == "Exit":
                self.clear_terminal()
                sys.exit()

            handler = self.option_handlers.get(selected_option, self.handle_default)
            if handler:
                result = handler()
                if result == "Back":
                    break
                elif result == "Exit":
                    self.clear_terminal()
                    sys.exit()
            else:
                print("Invalid option selected.")
                logging.warning(f"Invalid singleplayer menu option selected: {selected_option}")

    def handle_easy(self):
        return self.start_game(difficulty='Easy', size=5, history_file='txt_files/easy_game_history.txt')

    def handle_medium(self):
        return self.start_game(difficulty='Medium', size=6, history_file='txt_files/medium_game_history.txt')

    def handle_hard(self):
        return self.start_game(difficulty='Hard', size=7, history_file='txt_files/hard_game_history.txt')

    def handle_back(self):
        return "Back"

    def handle_default(self):
        print("This option is not yet implemented.")
        logging.warning("Attempted to access an undefined singleplayer handler.")
        return

    def start_game(self, difficulty, size, history_file):
        """
        Encapsulates the game starting logic for different difficulty levels.
        """
        username = input("Enter your username: ")
        user_board = Board(size, size)
        user_board.place_ships_random()

        ai_board = Board(size, size)
        ai_board.place_ships_random()

        targeting_system = TargetingSystem(ai_board)
        ai = PseudoAI(ai_board, user_board)

        game_result = game_loop(user_board, ai_board, targeting_system, ai)

        # Store instantly in a txt file
        with open(history_file, 'a') as file:
            timenow = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            game_result.insert(0, timenow)
            game_result.insert(0, username)
            file.write(f"{game_result}\n")

        input("\nPress Enter to continue...")
        return

# Entry Point
if __name__ == "__main__":
    main_menu = MainMenu()
    main_menu.handle_selection()

