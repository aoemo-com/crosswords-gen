#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os

import conf


def make_file_dirs(file_path):
    """为文件创建目录"""
    path = os.path.split(file_path)[0]
    if path and not os.path.exists(path):
        os.makedirs(path)


def gen_lang(lang):
    print(f"正在生成语言:{lang}...")

    def init_words() -> list:
        words = []
        dict_filename = f"dicts/{lang}.csv"
        with open(dict_filename) as dict_file:
            words_set = set()
            freq = 1
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
                words.append((lower_word, freq))
                freq += 1
        return words

    all_words = init_words()

    def gen_words(
            seed_word: str,
            max_freq: int,
            min_count: int,
            min_len: int) -> (list, int):

        words = []
        sum_freq = 0
        for word, freq in all_words[:max_freq]:
            if len(word) < min_len or word == seed_word:
                continue

            lower_chars_copy = list(seed_word)
            for char in word:
                if not lower_chars_copy:
                    break
                if char not in lower_chars_copy:
                    break
                lower_chars_copy.remove(char)
            else:
                words.append(word)
                sum_freq += freq

        if len(words) + 1 < min_count:
            return [], 0
        return words, sum_freq

    output_filename = f"output/{lang}.csv"
    make_file_dirs(output_filename)

    def gen_levels(
            output_file,
            used_seed_words: set,
            batch_level: int,
            start_level: int,
            end_level: int,
            words_max_freq: int,
            seed_word_max_len: int,
            arrange_word_cnt: int,
            gen_words_min_count: int,
            gen_words_min_len: int
    ):
        # print(f"正在生成关卡{start_level}-{end_level}:")

        # 频率限制
        seed_words = all_words[:words_max_freq]
        # 长度限制
        seed_words = [(word, _) for word, _ in seed_words if seed_word_max_len >= len(word)]
        # 重复限制
        seed_words = [(word, _) for word, _ in seed_words if word not in used_seed_words]

        if start_level == 1:
            headers = [
                "批号",
                "序号",
                "参:最小长度",
                "参:最大长度",
                "参:最小数量",
                "参:词频上限",
                "猜词数",
                "全部词数",
                "种子词",
                "种子词频率",
                "种子词长度",
                "其他词总频率",
                "其他词总长度",
                "频率系数",
                "数量系数",
                "长度系数",
                "难度系数",
                "其他词",
            ]
            output_file.write(",".join(headers) + "\n")
        level_count = 0
        need_level_count = end_level - start_level + 1
        for seed_word, seed_word_freq in seed_words:
            words, sum_freq = gen_words(
                seed_word,
                words_max_freq,
                gen_words_min_count,
                gen_words_min_len
            )
            if words:
                used_seed_words.add(seed_word)
                output_columns = (
                    batch_level,  # 批号
                    start_level + level_count,  # 序号
                    gen_words_min_len,  # 参:最小长度
                    seed_word_max_len,  # 参:最大长度
                    gen_words_min_count,  # 参:最小数量
                    words_max_freq,  # 参:词频上限
                    arrange_word_cnt,  # 猜词数
                    len(words) + 1,  # 全部词数
                    seed_word,  # 种子词
                    seed_word_freq,  # 种子词频率
                    len(seed_word),  # 种子词长度
                    sum_freq,  # 其他词总频率
                    sum(len(word) for word in words),  # 其他词总长度
                    "",  # 频率系数
                    "",  # 数量系数
                    "",  # 长度系数
                    "",  # 难度系数
                    *words,  # 其他词
                )
                output_columns = [str(_) for _ in output_columns]
                output_file.write(",".join(output_columns) + "\n")
                print("\t".join(output_columns))
                level_count += 1
                if level_count >= need_level_count:
                    break
        assert level_count >= need_level_count, f"只能生成{level_count}个关卡! 请放宽生成等级配置..."

    with open(output_filename, "w") as output:
        last_start_level = 1
        used_words = set()
        for batch, levels_conf in enumerate(conf.LEVELS):
            assert levels_conf[0] >= last_start_level
            gen_levels(
                output,
                used_words,
                batch + 1,
                last_start_level,
                *levels_conf
            )
            last_start_level = levels_conf[0] + 1


def main():
    for lang in conf.LANGUAGES:
        gen_lang(lang)


if __name__ == "__main__":
    main()
