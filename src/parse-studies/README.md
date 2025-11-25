# Parse studies JSON file

This folder parses JSON files present in data/studies/combined-studies. Each JSON file contains multiple studies.
Each study is stored in a separate file in data/studies/split-studies. The name of the file will be the nctid of the file.
E.g. data/studies/split-studies/NCT06779357.json

## Run

uv run main.py