#!/usr/bin/env python
# -*- coding:utf-8 -*-

import multiprocessing as mp
import os
import time

import conf


def make_file_dirs(file_path):
    """为文件创建目录"""
    path = os.path.split(file_path)[0]
    if path and not os.path.exists(path):
        os.makedirs(path)


def gen_lang(lang, queue):
    """生成一个语言数据"""
    try:
        start_time = time.time()
        print("语言%s: 正在生成..." % lang)

        def init_words():
            """单词初始化"""
            words = []
            dict_filename = "dicts/%s.csv" % lang
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
                    words.append(lower_word)
                    freq += 1
            return words

        # 全部单词, list(str)
        all_words = init_words()

        def gen_levels(
                output_file,
                used_seed_words,
                batch_level,
                start_level,
                end_level,
                words_max_freq,
                seed_word_max_len,
                arrange_word_cnt,
                gen_words_min_len
        ):
            """根据一个关卡的等级配置生成等级数据"""

            # 频率限制
            seed_words = all_words[:words_max_freq]
            # 长度限制
            seed_words = [
                (word, i + 1) for i, word in enumerate(seed_words)
                if seed_word_max_len >= len(word) >= max(3, gen_words_min_len)
            ]
            # 重复限制
            seed_words = [(word, _) for word, _ in seed_words if word not in used_seed_words]

            if start_level == 1:
                headers = [
                    "批号",
                    "序号",
                    "参:最小长度",
                    "参:最大长度",
                    "参:词频上限",
                    "参:猜词数",
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
            # 频率限制
            filtered_words = all_words[:words_max_freq]
            # 长度限制
            filtered_words = [
                (word, i + 1) for i, word in enumerate(filtered_words)
                if seed_word_max_len >= len(word) >= gen_words_min_len
            ]
            filtered_words_chars_count = {
                word: {
                    char: word.count(char) for char in word
                } for word, _ in filtered_words
            }

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
                    output_columns = [
                        batch_level,  # 批号
                        start_level + level_count,  # 序号
                        gen_words_min_len,  # 参:最小长度
                        seed_word_max_len,  # 参:最大长度
                        words_max_freq,  # 参:词频上限
                        arrange_word_cnt,  # 参:猜词数
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
                        ";".join(words),  # 其他词
                    ]
                    output_columns = [str(_) for _ in output_columns]
                    output_file.write(",".join(output_columns) + "\n")
                    print("\t".join([
                                        lang,
                                        str(batch_level),
                                        str(start_level + level_count),
                                        seed_word]
                                    + words))
                    level_count += 1
                    if level_count >= need_level_count:
                        break
            assert level_count >= need_level_count, \
                "关卡[%d-%d]: 只能生成%d个关卡! 请放宽生成等级配置..." % (
                    start_level, end_level, level_count
                )

        output_filename = "output/%s.csv" % lang
        make_file_dirs(output_filename)
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
        used_time = time.time() - start_time
        print("语言%s: 生成完成, 用时:%.2f秒." % (lang, used_time))
        queue.put(True)
    except Exception as e:
        print("语言%s: 生成异常: %s" % (lang, e))
        queue.put(False)


def main():
    """全部语言生成"""
    pool = mp.Pool()
    queue = mp.Manager().Queue()
    for lang in conf.LANGUAGES:
        pool.apply_async(gen_lang, args=(lang, queue))
    pool.close()
    for _ in range(len(conf.LANGUAGES)):
        if not queue.get():
            exit(1)
    pool.join()


if __name__ == "__main__":
    main()
