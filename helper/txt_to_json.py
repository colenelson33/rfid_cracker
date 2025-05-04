#!/usr/bin/env python3
import json
import re

INPUT = './../config/keys.txt'
OUTPUT = './../config/keys.json'

def load_keys(path):
    keys = []
    with open(path, 'r') as f:
        for line in f:
            # Remove anything after a '#' (inline or full-line comment)
            line = re.split(r'#', line, 1)[0].strip()
            if not line:
                continue
            # Expect exactly 12 hex chars
            if re.fullmatch(r'[0-9A-Fa-f]{12}', line):
                keys.append(line.upper())
            else:
                print(f"Skipping invalid line: {line}")
    return keys

def main():
    keys = load_keys(INPUT)
    with open(OUTPUT, 'w') as f:
        json.dump(keys, f, indent=2)
    print(f"Wrote {len(keys)} keys to {OUTPUT}")

if __name__ == '__main__':
    main()
