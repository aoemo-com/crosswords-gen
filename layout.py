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

    def area(self):
        return self.width * self.height

    def __contains__(self, point):
        """点是否在范围内"""
        x, y = point
        return self.left <= x < self.right and self.top <= y < self.bottom

    def __ior__(self, other):
        """并集"""
        self.left = min(self.left, other.left)
        self.top = min(self.top, other.top)
        self.right = max(self.right, other.right)
        self.bottom = max(self.bottom, other.bottom)
        return self

    def __or__(self, other):
        """并集返回新矩形"""
        return IntRect(
            min(self.left, other.left),
            min(self.top, other.top),
            max(self.right, other.right),
            max(self.bottom, other.bottom),
        )

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

    def __iter__(self):
        """从中心螺旋向外迭代"""

        x_offset = (self.left + self.right) / 2.0
        y_offset = (self.top + self.bottom) / 2.0
        x, y, dx, dy = 0, 0, 0, -1
        # 迭代多一圈, 防止 高宽不整除2 问题
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

        def __init__(self, word, x, y, horizontal):
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
            # 与其他单词相交的次数
            self.intersect_cnt = 0

        def can_intersect(self):
            """能否与其他单词相交: 不能用满，否则单词就被隐藏了"""
            return self.intersect_cnt + 1 < len(self.word)

        def add_intersect(self, other):
            """增加单词相交"""
            self.intersect_cnt += 1
            other.intersect_cnt += 1

        def print_layout(self, board, x, y, word_rewrite_callback):
            """输出到二维数组内"""
            for char in word_rewrite_callback(self.word):
                board[y][x] = char
                x, y = x + [0, 1][self.horizontal], y + [1, 0][self.horizontal]

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

    def __init__(
            self,
            layout_count,  # 需要排列的数量
            key_word,  # 必须排列的关键单词
            other_words,  # 其他可选单词
            max_width=0,  # 最大宽度(默认无限制)
            max_height=0  # 最大高度(默认无限制)
    ):
        # 需要排列的数量
        assert layout_count >= 2
        self.layout_count = layout_count
        # 词表: 关键单词排第一位
        self.words = list(other_words)
        if key_word:
            self.words[:0] = [key_word]
        assert len(self.words) >= layout_count

        # 矩形范围的宽高限制
        assert \
            isinstance(max_width, int) and \
            isinstance(max_height, int) and \
            max_width >= 0 and \
            max_height >= 0 and \
            "max_width:%d or max_height:%d invalid!" % (max_width, max_height)
        # 是否有宽高限制
        self.have_rect_limit = max_width > 0 or max_height > 0
        # 实际宽高限制
        self._real_rect_max_width = max_width or 999999999
        self._real_rect_max_height = max_height or 999999999

        # 全部单词排列的最大矩形范围
        self.rect = IntRect()

        # 单词排列 [WordLayout]
        self.word_layouts = []

        # 在矩形区域外部找排列位置的当前(顺时针)方位循环索引
        # 0.同向: 水平方向水平排, 垂直方向垂直排, 与矩形相连接
        # 1.同向: 水平方向水平排, 垂直方向垂直排, 与矩形不相连
        # 2.反向: 水平方向垂直排, 垂直方向水平排, 与矩形不相连
        self.outside_layout_poses = [0, 0, 0]

        self.do_layout()

    def layout_words(self):
        """返回排列好的单词"""
        return [layout.word for layout in self.word_layouts]

    def check_and_add_word_layout(self, word, x, y, horizontal, inserted_layout=None):
        """测试单词是否可以排入，可以则排入"""
        new_layout = self.WordLayout(word, x, y, horizontal)

        if self.have_rect_limit:
            new_rect = self.rect | new_layout.rect
            if new_rect.width > self._real_rect_max_width or \
                    new_rect.height > self._real_rect_max_height:
                return False

        passed_layouts = set()  # 经过相交的单词排列
        if self.check_word_layout(new_layout, inserted_layout, passed_layouts):
            self.word_layouts.append(new_layout)
            self.rect |= new_layout.rect
            # 增加所有相交(插入/被插入/经过)单词排列的相交
            if inserted_layout:
                for layout in [inserted_layout] + list(passed_layouts):
                    layout.add_intersect(new_layout)
            return True
        return False

    def check_word_layout(self, new_layout, inserted_layout, passed_layouts):
        """单词是否可以排入"""

        new_rect = new_layout.rect
        left, top, right, bottom = \
            new_rect.left, new_rect.top, new_rect.right, new_rect.bottom
        horizontal = new_layout.horizontal

        # 新单词排列的危险矩形区域
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
        # 已有单词排列 不能和 新单词排列的危险矩形区域 有冲突
        for layout in self.word_layouts:
            # (插入): 跳过正在尝试插入的单词
            if layout is inserted_layout:
                continue
            for danger_rect in danger_rectangles:
                if layout.rect & danger_rect:
                    # 不插入
                    if not inserted_layout:
                        return False
                    # 插入: 同向
                    elif layout.horizontal == horizontal:
                        # 像以下的情况, as应该和saw的a连在一起
                        #
                        #   was
                        #     a
                        #     w
                        #
                        # saw可以相交
                        # saw和was的矩形相交
                        # was与危险矩形相交只有1个格子
                        if not (inserted_layout.can_intersect() and
                                layout.rect & inserted_layout.rect and
                                layout.rect.intersect(danger_rect).area() == 1):
                            return False
                    # 插入: 反向
                    else:
                        # 旧单词可以相交
                        # 旧单词和新单词的相交，交点字母一样
                        if not (layout.can_intersect() and new_layout & layout):
                            return False
                        # 经过相交的单词排列
                        passed_layouts.add(layout)
        return True

    def layout_word_not_insert(self, word):
        """排列一个单词, 不插入"""

        # 在矩形区域内找位置, 从里到外螺旋旋转
        for x, y in self.rect:
            if self.check_and_add_word_layout(word, x, y, horizontal=True) or \
                    self.check_and_add_word_layout(word, x, y, horizontal=False):
                return True

        # 在矩形区域相连的外部4边循环排列
        positions_array = [
            # 0.同向: 水平方向水平排, 垂直方向垂直排, 与矩形相连
            [
                (self.rect.left, self.rect.top - 1, True),
                (self.rect.right - len(word), self.rect.top - 1, True),

                (self.rect.right, self.rect.top, False),
                (self.rect.right, self.rect.bottom - len(word), False),

                (self.rect.right - len(word), self.rect.bottom, True),
                (self.rect.left, self.rect.bottom, True),

                (self.rect.left - 1, self.rect.bottom - len(word), False),
                (self.rect.left - 1, self.rect.top, False),
            ],
            # 1.同向: 水平方向水平排, 垂直方向垂直排, 与矩形不相连
            [
                (self.rect.left, self.rect.top - 2, True),
                (self.rect.right + 1, self.rect.top, False),
                (self.rect.left, self.rect.bottom + 1, True),
                (self.rect.left - 2, self.rect.top, False),
            ],
            # 2.反向: 水平方向垂直排, 垂直方向水平排, 与矩形不相连
            [
                (self.rect.left, self.rect.top - 1 - len(word), False),
                (self.rect.right + 1, self.rect.top, True),
                (self.rect.left, self.rect.bottom + 1, False),
                (self.rect.left - 1 - len(word), self.rect.top, True),
            ],
        ]
        for pos_index, positions in enumerate(positions_array):
            for _ in range(len(positions)):
                x, y, horizontal = \
                    positions[self.outside_layout_poses[pos_index] % len(positions)]
                self.outside_layout_poses[pos_index] += 1
                if self.check_and_add_word_layout(word, x, y, horizontal):
                    return True
        assert 0, "NOT ENOUGH max_width or max_height!"

    def layout_word(self, word):
        """排列一个单词, 插入"""

        # 检测每个已经排列的单词与新单词的相同字母和双方对应的索引
        for layout in self.word_layouts:

            layout_word = layout.word
            horizontal = layout.horizontal
            left, top = layout.rect.left, layout.rect.top

            for char_index, char in enumerate(word):
                for layout_char_index, layout_char in enumerate(layout_word):
                    if char == layout_char:
                        # 根据双方索引设置插入点位置
                        x, y = (left + layout_char_index, top - char_index) if horizontal \
                            else (left - char_index, top + layout_char_index)
                        if self.check_and_add_word_layout(
                                word, x, y, not horizontal, inserted_layout=layout):
                            return True
        return False

    def do_layout(self):
        """排列"""

        # 第一个单词排在(0, 0), 如果宽度不够，则转为垂直
        assert self.check_and_add_word_layout(
            self.words[0], x=0, y=0,
            horizontal=self._real_rect_max_width >= len(self.words[0])
        )

        left_words = self.words[1:]
        while len(left_words) > len(self.words) - self.layout_count:
            # 从 待排单词 里循环找可以插入式排列的
            for word in left_words:
                if self.layout_word(word):
                    left_words.remove(word)
                    break
            # 找不到
            else:
                # 排一个不插入的
                self.layout_word_not_insert(left_words[0])
                left_words.remove(left_words[0])

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

        # 右上/左下打印宽/高
        board[0][-len(str(self.rect.width)):] = str(self.rect.width)
        board[-1][:len(str(self.rect.height))] = str(self.rect.height)

        # 先打印隐藏的/再打印显示的
        words = list(prior_words)
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
        CrosswordLayout(
            level.count,
            level.seed_word,
            level.other_words,
            # max_width=30,
            # max_height=20,
        ).print_layout()
    print("finished in %.3fs" % (time.time() - start))

    # level = levels[1]
    # CrosswordLayout(level.count, level.seed_word, level.other_words).print_layout()
