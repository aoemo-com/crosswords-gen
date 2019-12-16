#!/usr/bin/env python
# -*- coding:utf-8 -*-

# Convert keyboard languages' dictionary

import json
import string


def pretty_dumps(d, sort_keys=True, indent=4):
    """pretty dumps for dict"""
    return json.dumps(d, sort_keys=sort_keys, indent=indent, ensure_ascii=False)


LANG = "NL"

DICT_INPUT_FILE = "main_%s.combined" % LANG.lower()
DICT_OUTPUT_FILE = "%s.csv" % LANG.upper()

BASIC_CHARS = string.ascii_lowercase
EXTRA_CHARS = "äçèéêëïöü"
ALL_CHARS = set(
    BASIC_CHARS.lower() + BASIC_CHARS.upper() +
    EXTRA_CHARS.lower() + EXTRA_CHARS.upper()
)

invalid_chars = {}
output_file = open(DICT_OUTPUT_FILE, "w")
count = 0
for line in open(DICT_INPUT_FILE):
    line = line.strip()
    if line.startswith("word="):
        columns = line.split(",")
        word = columns[0][5:]
        invalid_char_found = False
        for char in word:
            if char not in ALL_CHARS:
                invalid_chars[char.lower()] = invalid_chars.get(char.lower(), 0) + 1
                invalid_char_found = True
        if not invalid_char_found:
            freq = int(columns[1][2:])
            output_file.write("%s,%d\n" % (word, freq))
            count += 1

print(pretty_dumps(invalid_chars))
print(count)
