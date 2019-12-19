#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""Generator
"""

import multiprocessing as mp
import os
import time
import sys

import conf


def make_file_dirs(file_path):
    """make all file dirs for a full filepath"""
    path = os.path.split(file_path)[0]
    if path and not os.path.exists(path):
        os.makedirs(path)


def init_words(lang):
    """initialize words"""
    words = []
    dict_filename = "dicts/%s.csv" % lang
    with open(dict_filename) as dict_file:
        words_set = set()
        for line in dict_file:
            word = line.strip().split(",")[0]
            lower_word = word.lower()
            word_len = len(word)
            if word_len <= 1:
                continue
            if word_len != len(lower_word) or word_len != len(word.upper()):
                continue
            if lower_word in words_set:
                continue
            words_set.add(lower_word)
            words.append(lower_word)
    return words


def gen_levels(
        lang,
        all_words,
        output_file,
        used_seed_words,
        batch_level,
        start_level,
        levels_conf
):
    """generate levels data by a batch of levels generating parameters"""

    end_level, words_max_freq, seed_word_max_len, arrange_word_cnt, gen_words_min_len = \
        levels_conf

    # freq limit
    seed_words = all_words[:words_max_freq]
    # len limit
    seed_words = [
        (word, i + 1) for i, word in enumerate(seed_words)
        if seed_word_max_len >= len(word) >= max(3, gen_words_min_len)
    ]
    # unique limit
    seed_words = [(word, _) for word, _ in seed_words if word not in used_seed_words]

    if start_level == 1:
        output_file.write(",".join(
            [
                "Batch",
                "No",
                "Param:max length",
                "Param:max length",
                "Param:max freq",
                "Param:guest word count",
                "All word count",
                "Seed word",
                "Seed word freq",
                "Seed word len",
                "Sum freq of the other words",
                "Sum len of the other words",
                "Freq factor",
                "Count factor",
                "Len factor",
                "Difficulty",
                "The other words",
            ]
        ) + "\n")

    # freq limit
    filtered_words = all_words[:words_max_freq]
    # len limit
    filtered_words = [
        (word, i + 1) for i, word in enumerate(filtered_words)
        if seed_word_max_len >= len(word) >= gen_words_min_len
    ]
    filtered_words_chars_count = {
        word: {
            char: word.count(char) for char in word
        } for word, _ in filtered_words
    }

    def gen_levels_internal():
        """generate levels internal"""

        current_level = start_level

        for seed_word, seed_word_freq in seed_words:
            words = []
            sum_freq = 0
            seed_word_chars_count = {char: seed_word.count(char) for char in seed_word}

            for word, freq in filtered_words:
                if word == seed_word:
                    continue
                word_chars_count = filtered_words_chars_count[word]
                if all(seed_word_chars_count.get(char, 0) >= count
                       for char, count in word_chars_count.items()):
                    words.append(word)
                    sum_freq += freq

            if len(words) + 1 >= arrange_word_cnt:
                used_seed_words.add(seed_word)
                output_file.write(",".join(
                    "%s" % _ for _ in [
                        batch_level,
                        current_level,
                        gen_words_min_len,
                        seed_word_max_len,
                        words_max_freq,
                        arrange_word_cnt,
                        len(words) + 1,
                        seed_word,
                        seed_word_freq,
                        len(seed_word),
                        sum_freq,
                        sum(len(word) for word in words),
                        "", "", "", "",
                        ";".join(words),
                    ]
                ) + "\n")
                print("\t".join(
                    [
                        lang,
                        str(batch_level),
                        str(current_level),
                        seed_word
                    ] + words
                ))
                if current_level >= end_level:
                    break
                current_level += 1

        if current_level < end_level:
            raise Exception(
                "Level[%d-%d]: can generate %d level(s) ONLY! "
                "Need WIDER generating parameters..." % (
                    start_level, end_level, current_level - start_level
                )
            )

    gen_levels_internal()


def gen_lang(lang, queue):
    """generate data for a language"""
    try:
        start_time = time.time()
        print("Lang: %s: generating..." % lang)
        # list(str)
        all_words = init_words(lang)

        output_filename = "output/%s.csv" % lang
        make_file_dirs(output_filename)
        with open(output_filename, "w") as output:
            last_start_level = 1
            used_words = set()
            for batch, levels_conf in enumerate(conf.LEVELS):
                gen_levels(
                    lang,
                    all_words,
                    output,
                    used_words,
                    batch + 1,
                    last_start_level,
                    levels_conf
                )
                last_start_level = levels_conf[0] + 1
        used_time = time.time() - start_time
        print("Lang: %s: generated in:%.2fs." % (lang, used_time))
        queue.put(True)
    except Exception as e:
        print("Lang: %s: EXCEPTION: %s!" % (lang, e))
        queue.put(False)


def main():
    """generate all languages"""
    pool = mp.Pool()
    queue = mp.Manager().Queue()
    for lang in conf.LANGUAGES:
        pool.apply_async(gen_lang, args=(lang, queue))
    pool.close()
    for _ in range(len(conf.LANGUAGES)):
        if not queue.get():
            sys.exit(1)
    pool.join()


if __name__ == "__main__":
    main()
