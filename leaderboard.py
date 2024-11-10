import ast  # to convert txt in file to actual list
import re

def time_to_seconds(time_str):
    hours, minutes, seconds = map(int, time_str.split(':'))
    total_seconds = hours * 3600 + minutes * 60 + seconds
    return total_seconds

def read_records(file_path):
    records = []
    with open(file_path, 'r') as file:
        # Skip the first two lines
        next(file)
        next(file)

        for line in file:
            line = line.strip()
            if not line:
                continue  # Skip empty lines
            try:
                # Convert the string representation of the list to an actual list
                record = ast.literal_eval(line)
                if record[2] == None:
                    next(file)
                    raise ValueError
                records.append(record)
            except Exception as e:
                #print(f"Error parsing line: {line}\n{e}")
                continue
    return records

def time_conversion_decorator(func):
    def wrapper(records):
        for record in func(records):
            total_seconds = time_to_seconds(record[4])
            record.append(total_seconds)  # Append total seconds
            yield record
    return wrapper

@time_conversion_decorator
def process_records(records):
    for record in records:
        yield record

def leaderboard_main(file_path):
    records = read_records(file_path)
    processed_records = list(process_records(records))

    # Sort based on the last element (total seconds)
    sorted_records = sorted(processed_records, key=lambda x: (x[-2],x[-1]))

    # Remove the total seconds before printing, if desired
    for idx, record in enumerate(sorted_records):
        record_without_seconds = str(record[:-1])  # Exclude the total_seconds

        pattern = re.compile(r"[\'\[\]]")
        formatted_record = pattern.sub('', record_without_seconds).strip()

        print(f"{idx+1}. {formatted_record}")

if __name__ == '__main__':
    filepath = 'easy_game_history.txt'
    leaderboard_main(filepath)
