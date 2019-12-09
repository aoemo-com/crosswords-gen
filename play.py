#!/usr/bin/env python
# -*- coding:utf-8 -*-

from collections import namedtuple
import random
import time
import os
import sys

python_version = sys.version_info
if python_version < (3, 0):
    input_func = raw_input
else:
    input_func = input

# 语言
LANGUAGE = "EN"
# 关卡配置文件
LEVELS_FILE_PATH = "%s.csv" % LANGUAGE

# 等级信息
Level = namedtuple(
    "Level",
    [
        "level",
        "chars",
        "words",
        "bonus_words",
        "finished_words",
        "finished_bonus_words",
    ]
)

# 所有等级
levels = []
# 等级初始化
with open(LEVELS_FILE_PATH) as levels_file:
    for level, line in enumerate(levels_file):
        if level == 0:
            continue

        columns = line.split(",")

        guess_words_count = int(columns[5])
        all_words_count = int(columns[6])
        seed_word = columns[7]

        all_words = [seed_word] + columns[16: 16 + all_words_count - 1]
        words = all_words[:guess_words_count]
        bonus_words = all_words[guess_words_count:]

        chars = [char for char in seed_word]
        random.shuffle(chars)
        levels.append(
            Level(level, chars, words, bonus_words, [], [])
        )

# 当前等级
current_level_index = 0
# 显示答案
show_answer = False
# 大小写方式
case = "upper"

while True:

    current_level = levels[current_level_index]


    def change_case(string):
        """根据case进行显示"""
        if case == "upper":
            return string.upper()
        elif case == "lower":
            return string.lower()
        elif case == "capital":
            return string.capitalize()
        return string

    def clear_screen():
        """清屏"""
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')


    def print_level():
        """打印当前等级信息"""
        clear_screen()
        print("")
        for word in current_level.words:
            if word in current_level.finished_words or show_answer:
                print(change_case(word))
            else:
                print("*" * len(word))

        status = "Stage: %d/%d" % (current_level_index + 1, len(levels))
        if current_level.bonus_words:
            status += " BonusWords: %d/%d" % (
                len(current_level.finished_bonus_words),
                len(current_level.bonus_words)
            )
        print(status)

        if current_level.bonus_words:
            if show_answer:
                print("BonusWords: %s" % " ".join(
                    change_case(word) for word in current_level.bonus_words
                ))
            elif current_level.finished_bonus_words:
                print("BonusWords: %s" % " ".join(
                    change_case(word) for word in current_level.finished_bonus_words
                ))

        print("")
        print("Chars: %s" % " ".join(change_case(char) for char in current_level.chars))
        print("")


    print_level()

    # 输入
    print("Input /help for help.")
    input_line = input_func("Input: ").strip()

    input_word = input_line.lower()
    # 单词命中
    if input_word in current_level.words and input_word not in current_level.finished_words:
        current_level.finished_words.append(input_word)
        if len(current_level.finished_words) >= len(current_level.words):
            print_level()
            input_func("Stage %d pass!\nNext level...press ENTER to continue..." % (current_level_index + 1))
            current_level_index += 1
    # 奖励单词命中
    elif input_word in current_level.bonus_words and input_word not in current_level.finished_bonus_words:
        current_level.finished_bonus_words.append(input_word)
    elif input_line == "/help":
        print("")
        print("Commands:")
        print("Quit:            /quit")
        print("Skip level:      /skip")
        print("Skip ### level:  /skip ###")
        print("Shuffle chars:   /shuffle")
        print("Show answer:     /show")
        print("Hide answer:     /hide")
        print("Upper case:      /upper")
        print("Lower case:      /lower")
        print("Capital case:    /capital")
        input_func("\nPress ENTER to continue...")
    elif input_line == "/quit":
        exit()
    elif input_line == "/shuffle":
        random.shuffle(current_level.chars)
    elif input_line in ("/show", "/hide"):
        show_answer = input_line == "/show"
    elif input_line.startswith("/skip"):
        skip_level = 1
        params = input_line[5:].strip().split(" ")
        if len(params) > 0 and params[0]:
            skip_level = int(params[0])
        current_level_index += skip_level
        current_level_index = max(0, current_level_index)
        current_level_index = min(current_level_index, len(levels) - 1)
        print("Enter level %d..." % (current_level_index + 1))
        time.sleep(1.0)
    elif input_line in ("/upper", "/lower", "/capital"):
        case = input_line[1:]
