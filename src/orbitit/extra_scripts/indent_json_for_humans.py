import json
import sys

def convert_json(filename):
    with open(filename, "r") as fd:
        data = json.load(fd)
    filename += "_indented.json"
    with open(filename, "w") as fd:
        json.dump(data, fd, indent=2)
    print(f"written {filename}")

for filename in sys.argv[1:]:
    convert_json(filename)
