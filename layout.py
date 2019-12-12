#!/usr/bin/env python
# -*- coding:utf-8 -*-


class Rect(object):
    def __init__(self, left, top, right, bottom):
        assert isinstance(left, int) and \
               isinstance(top, int) and \
               isinstance(right, int) and \
               isinstance(bottom, int) and \
               left < right and \
               top < bottom
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom

    @property
    def width(self):
        return self.right - self.left

    @property
    def height(self):
        return self.bottom - self.top

    def __contains__(self, point):
        """点是否在矩形内"""
        x, y = point
        return self.left <= x < self.right and self.top <= y < self.bottom

    def __ior__(self, other):
        """合并"""
        self.left = min(self.left, other.left)
        self.top = min(self.top, other.top)
        self.right = max(self.right, other.right)
        self.bottom = max(self.bottom, other.bottom)
        return self

    def __and__(self, other):
        """是否有交集"""
        return ((self.left <= other.left < self.right) or (other.left <= self.left < other.right)) and \
               ((self.top <= other.top < self.bottom) or (other.top <= self.top < other.bottom))

    def intersect(self, other):
        """交集"""
        min_right = min(self.right, other.right)
        min_bottom = min(self.bottom, other.bottom)
        if self.left <= other.left < self.right:
            if self.top <= other.top < self.bottom:
                return Rect(other.left, other.top, min_right, min_bottom)
            elif other.top <= self.top < other.bottom:
                return Rect(other.left, self.top, min_right, min_bottom)
        elif other.left <= self.left < other.right:
            if self.top <= other.top < self.bottom:
                return Rect(self.left, other.top, min_right, min_bottom)
            elif other.top <= self.top < other.bottom:
                return Rect(self.left, self.top, min_right, min_bottom)

    def spiral_iterate(self, callback, *args, **kwargs):
        """从中间螺旋向外访问回调"""
        width = self.width
        height = self.height
        x = y = 0
        x_offset = (self.left + self.right) // 2
        y_offset = (self.top + self.bottom) // 2
        dx = 0
        dy = -1
        for i in range(max(width, height) ** 2):
            if (-width / 2 < x <= width / 2) and (-height / 2 < y <= height / 2):
                callback_return = callback(x + x_offset, y + y_offset, *args, **kwargs)
                if callback_return:
                    return callback_return
            if x == y or (x < 0 and x == -y) or (x > 0 and x == 1 - y):
                dx, dy = -dy, dx
            x, y = x + dx, y + dy


class CrosswordLayout(object):
    class WordLayout(object):
        """单词排列"""

        def __init__(self, word, x, y, horizontal):
            # 单词
            self.word = word
            # 是否水平方向
            self.horizontal = horizontal
            # 矩形范围
            self.rect = Rect(
                x, y,
                x + [1, len(self.word)][horizontal],
                y + [len(self.word), 1][horizontal],
            )

        def output(self, board, x, y):
            """输出到二维数组内"""
            for char in self.word:
                board[y][x] = char
                x += [0, 1][self.horizontal]
                y += [1, 0][self.horizontal]

        def get_char(self, x, y):
            """取得坐标上的字符"""
            assert (x, y) in self.rect
            offset = [y - self.rect.top, x - self.rect.left][self.horizontal]
            return self.word[offset]

    def __init__(self, count, key_word, other_words):
        # 数量
        assert count >= 2
        self.count = count
        # 词表: 关键词排第一位, 其他按长度从大到小
        self.words = []
        if key_word:
            self.words += [key_word]
        self.words += sorted(other_words, key=len, reverse=True)
        assert len(self.words) >= count
        # 矩形范围
        self.rect = Rect(0, 0, 1, 1)
        # 单词排列
        self.word_layouts = []
        # 在矩形区域外找排列位置的当前方位索引
        self.outside_layout_pos = 0
        # 排列
        self.layout()

    def add_word_layout(self, word, x, y, horizontal=True):
        """增加一个单词排列"""
        layout = self.WordLayout(word, x, y, horizontal)
        self.word_layouts.append(layout)
        self.rect |= layout.rect

    def can_word_layout(self, word, x, y, horizontal=True, insert=True):
        """单词是否可以排入"""

        new_layout = self.WordLayout(word, x, y, horizontal)
        rect = new_layout.rect
        # 危险矩形区域的 左上右下 偏移
        danger_rectangles = [
            [
                Rect(rect.left + 0, rect.top - 1, rect.right + 0, rect.bottom + 1),
                Rect(rect.left - 1, rect.top + 0, rect.right + 1, rect.bottom + 0),
            ],
            [
                Rect(rect.left - 1, rect.top + 0, rect.right + 1, rect.bottom + 0),
                Rect(rect.left + 0, rect.top - 1, rect.right + 0, rect.bottom + 1),
            ]
        ][horizontal]

        # 同一个方向上的检测 #####################
        # 如果是水平方向, 不能和危险区域上的其他(水平/垂直)单词有矩形区域冲突
        # 垂直方向也类似
        for word_layout in self.word_layouts:
            for danger_rect in danger_rectangles:
                # 不插入则水平/垂直单词都检测
                # 插入直检测同向单词
                if (not insert or word_layout.horizontal == horizontal) and word_layout.rect & danger_rect:
                    return False
        # 不插入, 已经检查了水平/垂直位置上的危险区域上的其他单词
        if not insert:
            return True

        # 插入方式, 需要对另外一个方向上的单词进行检测
        # 另一个方向上的检测 #####################
        for word_layout in self.word_layouts:
            # 不同向的跳过
            if word_layout.horizontal == horizontal:
                continue
            word_rect = word_layout.rect
            for danger_rect in danger_rectangles:
                # 与危险矩形区域有交集
                if word_rect & danger_rect:
                    # 必须和新单词的矩形区域有交集，交点字母一样
                    common_rect = rect.intersect(word_rect)
                    if not common_rect:
                        return False
                    x, y = common_rect.left, common_rect.top
                    if word_layout.get_char(x, y) != new_layout.get_char(x, y):
                        return False
        return True

    def layout_word_not_insert(self, word):
        """排列一个单词, 不插入"""

        # 在矩形区域内找位置, 从里到外螺旋旋转
        def spiral_callback(x, y):
            """螺旋旋转迭代位置回调"""
            # 先水平排列测试
            if self.can_word_layout(word, x, y, insert=False):
                self.add_word_layout(word, x, y)
                return True
            # 再垂直排列测试
            if self.can_word_layout(word, x, y, False, insert=False):
                self.add_word_layout(word, x, y, False)
                return True
            return False

        # 螺旋旋转迭代
        ok = self.rect.spiral_iterate(spiral_callback)

        if not ok:
            # 在矩形区域外4边循环(上/右/下/左)排列
            positions = [
                (self.rect.left, self.rect.top - 2, True),
                (self.rect.right + 1, self.rect.top, False),
                (self.rect.left, self.rect.bottom + 1, True),
                (self.rect.left - 2, self.rect.top, False),
            ]
            self.add_word_layout(
                word,
                *positions[self.outside_layout_pos % len(positions)]
            )
            self.outside_layout_pos += 1
        return True

    def layout_word(self, word, insert=True):
        """排列一个单词"""

        # 不插入 #############################
        if not insert:
            return self.layout_word_not_insert(word)

        # 插入 ###############################
        # 检测每个已经排列的单词与新单词的相同字母和双方对应的索引
        for layout in self.word_layouts:
            layout_word = layout.word
            horizontal = layout.horizontal
            rect = layout.rect
            for offset1, char1 in enumerate(word):
                for offset2, char2 in enumerate(layout_word):
                    if char1 != char2:
                        continue
                    # 根据双方索引设置插入点位置
                    if horizontal:
                        x = rect.left + offset2
                        y = rect.top - offset1
                    else:
                        x = rect.left - offset1
                        y = rect.top + offset2
                    # 测试位置是否可以排列, 反向
                    if self.can_word_layout(word, x, y, not horizontal):
                        self.add_word_layout(word, x, y, not horizontal)
                        return True
        return False

    def layout(self):
        """排列"""

        # 第一个单词排在(0, 0)
        self.add_word_layout(self.words[0], 0, 0)
        # 待排单词
        words = self.words[1:]

        while len(words) > len(self.words) - self.count:
            # 从待排单词里找
            for word in words:
                # 是否可以排一个插入的
                if self.layout_word(word):
                    words.remove(word)
                    # 再排下一个
                    break
                # 不行, 试下一个
            # 全部都无法插入
            else:
                # 排一个不插入的
                self.layout_word(words[0], insert=False)
                words.remove(words[0])
            # 再排下一个

    def print_layout(self):
        """打印排列"""
        board_margin = 2
        board_width = self.rect.width + 2 * board_margin
        board_height = self.rect.height + 2 * board_margin
        board = [list(" " * board_width) for _ in range(board_height)]

        # 打印边框
        for y in range(board_height):
            board[y][0] = board[y][-1] = "|"
        for x in range(board_width):
            board[0][x] = board[-1][x] = "-"
        board[0][0] = \
            board[-1][0] = \
            board[0][-1] = \
            board[-1][-1] = "+"

        for layout in self.word_layouts:
            # 坐标转换到二维数组上
            board_x = layout.rect.left - self.rect.left + board_margin
            board_y = layout.rect.top - self.rect.top + board_margin
            layout.output(board, board_x, board_y)

        print("\n".join("".join(_) for _ in board))


if __name__ == "__main__":
    from collections import namedtuple
    import time

    # 等级信息
    Level = namedtuple(
        "Level",
        [
            "level",
            "count",
            "seed_word",
            "other_words",
        ]
    )
    # 所有等级
    levels = []
    # 等级初始化
    with open("EN.csv") as levels_file:
        for level, line in enumerate(levels_file):
            if level == 0:
                continue

            columns = line.split(",")

            guess_word_count = int(columns[5])
            seed_word = columns[7].strip()
            the_other_words = [word.strip() for word in columns[16].split(";") if word.strip()]
            levels.append(
                Level(level, guess_word_count, seed_word, the_other_words)
            )

    if 0:
        start = time.time()
        for level in levels:
            print(level.level)
            CrosswordLayout(level.count, level.seed_word, level.other_words).print_layout()
        print("finished in %.3fs" % (time.time() - start))

    if 1:
        level = levels[499]
        crossword = CrosswordLayout(level.count, level.seed_word, level.other_words)
        crossword.print_layout()
