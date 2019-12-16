#!/usr/bin/env python
# -*- coding:utf-8 -*-

# Simulator for game play

from collections import namedtuple
import random
import time
import os
import sys
import subprocess

from layout import CrosswordLayout

python_version = sys.version_info
if python_version < (3, 0):
    input_func = raw_input
else:
    input_func = input

# levels data file
LEVELS_FILE_PATH = "EN.csv"

Level = namedtuple(
    "Level",
    [
        "level",
        "chars",
        "words",
        "bonus_words",
        "layout",
        "finished_words",
        "finished_bonus_words",
    ]
)

all_levels = []
print("loading levels...")
# initialize all levels
with open(LEVELS_FILE_PATH) as levels_file:
    for level, line in enumerate(levels_file):
        if level == 0:
            continue

        columns = line.split(",")

        guess_words_count = int(columns[5])
        seed_word = columns[7].strip()
        other_words = [word.strip() for word in columns[16].split(";") if word.strip()]

        layout = CrosswordLayout(guess_words_count, seed_word, other_words)
        words = layout.layout_words()
        all_words = [seed_word] + other_words
        bonus_words = [word for word in all_words if word not in words]
        chars = [char for char in seed_word]
        random.shuffle(chars)
        all_levels.append(
            Level(level, chars, words, bonus_words, layout, [], [])
        )
        if level % 100 == 0:
            print(level)

current_level_index = 0
# current case for word display
case = "lower"

while True:

    current_level = all_levels[current_level_index]


    def change_case(word):
        """change word case by current case"""
        return word.upper() if case == "upper" else word.lower()


    def print_level():
        """print current level information"""
        subprocess.call(("clear", "cls")[os.name == "nt"])
        print("")

        def show_hide_word(word):
            """show/hide finished/unfinished words"""
            if word not in current_level.finished_words:
                return "*" * len(word)
            return word

        current_level.layout.print_layout(
            show_hide_word,
            # Print unfinished words first with '*'
            set(current_level.words) - set(current_level.finished_words),
        )

        # level state
        print("")
        print("Level: %d/%d" % (current_level_index + 1, len(all_levels)))
        if current_level.bonus_words:
            bonus_words_status = "Bonus words: %d/%d" % (
                len(current_level.finished_bonus_words),
                len(current_level.bonus_words)
            )
            bonus_words_status += " %s" % " ".join(
                change_case(word)
                if word in current_level.finished_bonus_words
                else "*" * len(word)
                for word in current_level.bonus_words
            )
            print(bonus_words_status)

        # characters
        print("")
        print("Chars: %s" % " ".join(change_case(char) for char in current_level.chars))
        print("")


    print_level()

    print("Input ? for help.")
    input_line = input_func("Input: ").strip()

    input_word = input_line.lower()
    # word matched
    if input_word in current_level.words and input_word not in current_level.finished_words:
        current_level.finished_words.append(input_word)
        if len(current_level.finished_words) >= len(current_level.words):
            print_level()
            input_func("Level %d pass!\nNext level...press ENTER to continue..." % (current_level_index + 1))
            current_level_index += 1
    # bonus word matched
    elif input_word in current_level.bonus_words and input_word not in current_level.finished_bonus_words:
        current_level.finished_bonus_words.append(input_word)
    elif input_line == "?":
        print("")
        print("Commands:")
        print("")
        print("Shuffle chars:   /shuffle")
        print("Lower case:      /lower")
        print("Upper case:      /upper")
        print("Skip level:      /skip")
        print("Skip ### level:  /skip ###")
        print("")
        input_func("Press ENTER to continue...")
    elif input_line == "/shuffle":
        random.shuffle(current_level.chars)
    elif input_line in ("/upper", "/lower"):
        case = input_line[1:]
    elif input_line.startswith("/skip"):
        skip_level = 1
        params = input_line[5:].strip().split(" ")
        if len(params) > 0 and params[0]:
            skip_level = int(params[0])
        current_level_index += skip_level
        current_level_index = max(0, current_level_index)
        current_level_index = min(current_level_index, len(all_levels) - 1)
        print("Enter level %d..." % (current_level_index + 1))
        time.sleep(1.0)
