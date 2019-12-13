#!/usr/bin/env python
# -*- coding:utf-8 -*-


class IntRect(object):
    """整数矩形, [左, 右), [上, 下) 半开区间"""

    def __init__(self, left=0, top=0, right=1, bottom=1):
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

    @property
    def area(self):
        return self.width * self.height

    def __contains__(self, point):
        """点是否在范围内"""
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
        return not (
                self.right <= other.left or
                other.right <= self.left or
                self.bottom <= other.top or
                other.bottom <= self.top
        )

    def intersect(self, other):
        """求交集"""
        if self & other:
            return IntRect(
                max(self.left, other.left),
                max(self.top, other.top),
                min(self.right, other.right),
                min(self.bottom, other.bottom)
            )

    def spiral_iter(self):
        """从中心螺旋向外迭代"""

        x_offset = (self.left + self.right) / 2.0
        y_offset = (self.top + self.bottom) / 2.0
        x, y, dx, dy = 0, 0, 0, -1

        for i in range(max(self.width + 2, self.height + 2) ** 2):
            point = int(x + x_offset), int(y + y_offset)
            if point in self:
                yield point
            if x == y or (x < 0 and x == -y) or (x > 0 and x == 1 - y):
                dx, dy = -dy, dx
            x, y = x + dx, y + dy


class CrosswordLayout(object):
    """crossword排列算法"""

    class WordLayout(object):
        """单词排列"""

        def __init__(self, word, x=0, y=0, horizontal=True):
            # 单词
            self.word = word
            # 是否水平方向
            self.horizontal = horizontal
            # 矩形范围
            self.rect = IntRect(
                x, y,
                x + [1, len(self.word)][horizontal],
                y + [len(self.word), 1][horizontal],
            )

        def print_layout(self, board, x, y, word_rewrite_callback):
            """输出到二维数组内"""
            # x, y方向增量
            dx, dy = (1, 0) if self.horizontal else (0, 1)
            for char in word_rewrite_callback(self.word):
                board[y][x] = char
                x, y = x + dx, y + dy

        def __getitem__(self, point):
            """取得坐标上的字符"""
            if point in self.rect:
                x, y = point
                offset = (x - self.rect.left) if self.horizontal else (y - self.rect.top)
                return self.word[offset]

        def __and__(self, other):
            """是否相交 且 交点坐标字母一样"""
            common = self.rect.intersect(other.rect)
            return common and self[common.left, common.top] == other[common.left, common.top]

    def __init__(self, layout_count, key_word, other_words):
        # 数量
        assert layout_count >= 2
        self.layout_count = layout_count
        # 词表: 关键词排第一位, 其他按长度从大到小
        self.words = sorted(other_words, key=len, reverse=True)
        if key_word:
            self.words[:0] = [key_word]
        assert len(self.words) >= layout_count

        # 全部单词排列的最大矩形范围
        self.rect = IntRect()
        # 单词排列 [WordLayout]
        self.word_layouts = []
        # 在矩形区域相连的外部找排列位置的当前(顺时针)方位循环索引
        self.connected_layout_pos = 0
        # 在矩形区域不相连的外部找排列位置的当前(顺时针)方位循环索引
        self.outside_layout_pos = 0

        # 排列
        self.layout()

    def layout_words(self):
        """返回排列好的单词"""
        return [word_layout.word for word_layout in self.word_layouts]

    def add_word_layout(self, word_layout):
        """增加一个单词排列"""
        self.word_layouts.append(word_layout)
        self.rect |= word_layout.rect

    def check_and_add_word_layout(self, word, x, y, horizontal, insert_layout=None):
        """测试单词是否可以排入，可以则排入"""
        word_layout = self.WordLayout(word, x, y, horizontal)
        if self.check_word_layout(word_layout, insert_layout):
            self.add_word_layout(word_layout)
            return True
        return False

    def check_word_layout(self, new_layout, insert_layout=None):
        """单词是否可以排入"""

        new_rect = new_layout.rect
        left, top, right, bottom = \
            new_rect.left, new_rect.top, new_rect.right, new_rect.bottom
        horizontal = new_layout.horizontal
        # 危险矩形区域
        if horizontal:
            danger_rectangles = [
                IntRect(left - 1, top + 0, right + 1, bottom + 0),
                IntRect(left + 0, top - 1, right + 0, bottom + 1),
            ]
        else:
            danger_rectangles = [
                IntRect(left + 0, top - 1, right + 0, bottom + 1),
                IntRect(left - 1, top + 0, right + 1, bottom + 0),
            ]

        # 不能和危险区域上的其他(水平/垂直)单词有矩形区域冲突
        for word_layout in self.word_layouts:
            for danger_rect in danger_rectangles:

                # 不插入: 水平/垂直单词都检测
                if not insert_layout:
                    if word_layout.rect & danger_rect:
                        return False

                # 插入: 只检测同向单词
                elif word_layout.horizontal == horizontal:
                    if word_layout.rect & danger_rect:
                        # 像以下的情况, as应该和saw的a连在一起
                        #
                        #   was
                        #     a
                        #   a w
                        #   s
                        #
                        # saw和was相交
                        # was与检测矩形相交只有1个格子
                        if word_layout.rect & insert_layout.rect and \
                                word_layout.rect.intersect(danger_rect).area == 1:
                            continue
                        return False

        # 插入方式, 需要对另外一个方向上的单词进行检测
        if insert_layout:
            for word_layout in self.word_layouts:

                # 正在尝试插入的单词的跳过
                # 同向的跳过
                if word_layout is insert_layout or word_layout.horizontal == horizontal:
                    continue

                for danger_rect in danger_rectangles:

                    # 与危险矩形区域有交集
                    if word_layout.rect & danger_rect:
                        # 必须和新单词的矩形区域有交集，交点字母一样
                        if not (new_layout & word_layout):
                            return False
        return True

    def layout_word_not_insert(self, word):
        """排列一个单词, 不插入"""

        # 在矩形区域内找位置, 从里到外螺旋旋转
        for x, y in self.rect.spiral_iter():
            # 先水平, 再垂直
            if self.check_and_add_word_layout(word, x, y, True) or \
                    self.check_and_add_word_layout(word, x, y, False):
                return True

        # 在矩形区域相连的外部4边的左、右循环(上2/右2/下2/左2)排列
        positions = [
            (self.rect.left, self.rect.top - 1, True),
            (self.rect.right - len(word), self.rect.top - 1, True),

            (self.rect.right, self.rect.top, False),
            (self.rect.right, self.rect.bottom - len(word), False),

            (self.rect.right - len(word), self.rect.bottom, True),
            (self.rect.left, self.rect.bottom, True),

            (self.rect.left - 1, self.rect.bottom - len(word), False),
            (self.rect.left - 1, self.rect.top, False),
        ]
        for _ in range(len(positions)):
            x, y, horizontal = positions[self.connected_layout_pos % len(positions)]
            self.connected_layout_pos += 1
            if self.check_and_add_word_layout(word, x, y, horizontal):
                break
        else:
            # 在矩形区域不相连的外部4边循环(上/右/下/左)排列
            positions = [
                (self.rect.left, self.rect.top - 2, True),
                (self.rect.right + 1, self.rect.top, False),
                (self.rect.left, self.rect.bottom + 1, True),
                (self.rect.left - 2, self.rect.top, False),
            ]
            x, y, horizontal = positions[self.outside_layout_pos % len(positions)]
            self.outside_layout_pos += 1
            self.add_word_layout(self.WordLayout(word, x, y, horizontal))
        return True

    def layout_word(self, word):
        """排列一个单词, 插入"""

        # 检测每个已经排列的单词与新单词的相同字母和双方对应的索引
        for layout in self.word_layouts:

            layout_word = layout.word
            horizontal = layout.horizontal
            left, top = layout.rect.left, layout.rect.top

            for word_char_index, word_char in enumerate(word):
                for layout_word_char_index, layout_word_char in enumerate(layout_word):

                    if word_char == layout_word_char:
                        # 根据双方索引设置插入点位置
                        if horizontal:
                            x = left + layout_word_char_index
                            y = top - word_char_index
                        else:
                            x = left - word_char_index
                            y = top + layout_word_char_index
                        # 测试位置是否可以插入排列, 反向
                        if self.check_and_add_word_layout(
                                word, x, y, not horizontal, insert_layout=layout):
                            return True
        return False

    def layout(self):
        """排列"""

        # 第一个单词排在(0, 0)
        self.add_word_layout(self.WordLayout(self.words[0]))
        # 待排单词
        words = self.words[1:]

        while len(words) > len(self.words) - self.layout_count:
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
                self.layout_word_not_insert(words[0])
                words.remove(words[0])
            # 再排下一个

    def print_layout(self, word_rewrite_callback=lambda word: word, prior_words=()):
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

        # 先打印隐藏的
        words = list(prior_words)
        # 再打印显示的
        words += [word for word in self.layout_words() if word not in words]
        # {单词: 排列}
        word_layouts_dict = {
            layout.word: layout for layout in self.word_layouts
        }

        for word in words:
            layout = word_layouts_dict[word]
            # 坐标转换到二维数组上
            board_x = layout.rect.left - self.rect.left + board_margin
            board_y = layout.rect.top - self.rect.top + board_margin
            layout.print_layout(board, board_x, board_y, word_rewrite_callback)

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
            the_other_words = [_word.strip() for _word in columns[16].split(";") if _word.strip()]
            levels.append(
                Level(level, guess_word_count, seed_word, the_other_words)
            )

    start = time.time()
    for level in levels:
        print(level.level)
        CrosswordLayout(level.count, level.seed_word, level.other_words).print_layout()
    print("finished in %.3fs" % (time.time() - start))

    # level = levels[4]
    # CrosswordLayout(level.count, level.seed_word, level.other_words).print_layout(word_rewrite)
