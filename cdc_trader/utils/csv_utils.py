import csv
from pathlib import Path

# Load from csv
def load_csv(file_path):
    with open(file_path, "r") as file:
        reader = csv.reader(file)
        data = list(reader)
    return data

# Load filepaths of csv files in a directory
def load_csv_files(folder_path,instruments=None, period='5m'):
    files = []
    for file in Path(folder_path).rglob("*.csv"):
        if period in str(file):
            # Load specific instruments
            if instruments!=None and str(file).split("\\")[1] in instruments:
                files.append(file)
            # Load all instruments
            elif not instruments:
                files.append(file)
    return files
