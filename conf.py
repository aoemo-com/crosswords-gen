#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""Configurations for gen.py
"""


# generating languages
LANGUAGES = [
    "EN",
    "RU",
    "ES",
    "FR",
    "IT",
    "TR",
    "DE",
    "PT",
    "NL",
]

# batches of levels generating parameters
LEVELS = [
    # end level
    #       max word freq
    #               max word len
    #                       guess word count
    #                               min word len
    [10,    1500,   3,      3,      2],
    [20,    2000,   4,      4,      2],
    [30,    2500,   5,      5,      3],
    [40,    3000,   5,      5,      3],
    [50,    3500,   6,      6,      3],
    [60,    4000,   6,      7,      3],
    [70,    4500,   7,      7,      4],
    [80,    5000,   7,      8,      4],
    [90,    5500,   8,      8,      4],
    [100,   6000,   8,      9,      4],
    [120,   6500,   9,     10,      5],
    [150,   7000,  10,     12,      5],
    [200,   7500,  11,     14,      5],
    [300,   8000,  12,     16,      5],
    [500,  10000,  14,     16,      6],
]
