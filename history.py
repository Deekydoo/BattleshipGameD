import re

# DECORATOR IN USE!

def read_file_generator(file_path):

    pattern = re.compile(r"[\'\[\]]")

    with open(file_path, 'r') as file:
        for line in file:
            formatted_line = pattern.sub('', line).strip()
            yield formatted_line

def print_read_file(file_path):
    for idx, line in enumerate(read_file_generator(file_path)):
        if idx >= 2:
            print(f"{idx-1}. {line}")

if __name__ == "__main__":

    # Usage example
    file_path = 'txt_files/easy_game_history.txt'

    print_read_file(file_path)


