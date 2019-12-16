#!/usr/bin/env python
# -*- coding:utf-8 -*-

# Crossword Layout


class IntRect(object):
    """Integer Rectangle, [left, right), [top, bottom)"""

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
        """Test if a point inside or not"""
        x, y = point
        return self.left <= x < self.right and self.top <= y < self.bottom

    def __ior__(self, other):
        """Merge another"""
        self.left = min(self.left, other.left)
        self.top = min(self.top, other.top)
        self.right = max(self.right, other.right)
        self.bottom = max(self.bottom, other.bottom)
        return self

    def __or__(self, other):
        """Merge another and return new one"""
        return IntRect(
            min(self.left, other.left),
            min(self.top, other.top),
            max(self.right, other.right),
            max(self.bottom, other.bottom),
        )

    def __and__(self, other):
        """Test if two rects have intersection or not"""
        return not (
                self.right <= other.left or
                other.right <= self.left or
                self.bottom <= other.top or
                other.bottom <= self.top
        )

    def intersect(self, other):
        """Return intersection"""
        if self & other:
            return IntRect(
                max(self.left, other.left),
                max(self.top, other.top),
                min(self.right, other.right),
                min(self.bottom, other.bottom)
            )

    def __iter__(self):
        """Spiral iteration from center to outside"""

        x_offset = (self.left + self.right) / 2.0
        y_offset = (self.top + self.bottom) / 2.0
        x, y, dx, dy = 0, 0, 0, -1
        # 1 round more prevents width/height NOT divided by 2
        for i in range(max(self.width + 2, self.height + 2) ** 2):
            point = int(x + x_offset), int(y + y_offset)
            if point in self:
                yield point
            if x == y or (x < 0 and x == -y) or (x > 0 and x == 1 - y):
                dx, dy = -dy, dx
            x, y = x + dx, y + dy


class CrosswordLayout(object):
    """Crossword Layout"""

    class WordLayout(object):
        """Word layout"""

        def __init__(self, word, x, y, horizontal):
            self.word = word
            self.horizontal = horizontal
            self.rect = IntRect(
                x, y,
                x + [1, len(self.word)][horizontal],
                y + [len(self.word), 1][horizontal],
            )
            # intersect count with other word(s' layouts)
            self.intersect_cnt = 0

        def can_intersect(self):
            """Can intersect with other or not"""
            # Word CAN NOT entirely intersects with other words
            # Otherwise this word will hided by others
            return self.intersect_cnt + 1 < len(self.word)

        def add_intersect(self, other):
            """Two words intersect"""
            self.intersect_cnt += 1
            other.intersect_cnt += 1

        def print_layout(self, board, x, y, word_rewrite_callback):
            """Output layout to a 2D array"""
            for char in word_rewrite_callback(self.word):
                board[y][x] = char
                x, y = x + [0, 1][self.horizontal], y + [1, 0][self.horizontal]

        def __getitem__(self, point):
            """Get char by point(x, y)"""
            if point in self.rect:
                x, y = point
                offset = (x - self.rect.left) if self.horizontal else (y - self.rect.top)
                return self.word[offset]

        def __and__(self, other):
            """Test if two layouts intersect with same char or not"""
            common = self.rect.intersect(other.rect)
            return common and self[common.left, common.top] == other[common.left, common.top]

    def __init__(
            self,
            layout_count,  # Word count need to be layout
            key_word,  # MUST layout word, seed word
            other_words,  # Other word choices
            max_width=0,  # 0 for unlimited
            max_height=0  # 0 for unlimited
    ):
        assert layout_count >= 2
        self.layout_count = layout_count
        self.words = list(other_words)
        if key_word:
            self.words[:0] = [key_word]
        assert len(self.words) >= layout_count

        # Width/height limit for rect
        assert \
            isinstance(max_width, int) and \
            isinstance(max_height, int) and \
            max_width >= 0 and \
            max_height >= 0 and \
            "max_width:%d or max_height:%d invalid!" % (max_width, max_height)
        # Have rect width/height limit or not
        self.have_rect_limit = max_width > 0 or max_height > 0
        # Real rect width/height limit
        self._real_rect_max_width = max_width or 999999999
        self._real_rect_max_height = max_height or 999999999

        # Rect for words' layouts
        self.rect = IntRect()

        # [self.WordLayout]
        # Layouts of words already layout
        self.word_layouts = []

        # Clock-wisely layout poses on the outer 4 sides of words' layouts rect
        # 0.same direction:
        #   horizontal layouts horizontally, vertical layouts vertically, connected to rect
        # 1.same direction:
        #   horizontal layouts horizontally, vertical layouts vertically, NOT connected to rect
        # 2.reversed direction:
        #   horizontal layouts vertically, vertical layouts horizontally, NOT connected to rect
        self.outside_layout_poses = [0, 0, 0]

        self.do_layout()

    def layout_words(self):
        """Return words already layout"""
        return [layout.word for layout in self.word_layouts]

    def check_and_add_word_layout(self, word, x, y, horizontal, inserted_layout=None):
        """Check if a word can be layout, and do it if YES"""
        new_layout = self.WordLayout(word, x, y, horizontal)

        if self.have_rect_limit:
            new_rect = self.rect | new_layout.rect
            if new_rect.width > self._real_rect_max_width or \
                    new_rect.height > self._real_rect_max_height:
                return False

        passed_layouts = set()
        if self.check_word_layout(new_layout, inserted_layout, passed_layouts):
            self.word_layouts.append(new_layout)
            self.rect |= new_layout.rect
            # Add intersect for all these(insert/inserted/passed) words
            if inserted_layout:
                for layout in [inserted_layout] + list(passed_layouts):
                    layout.add_intersect(new_layout)
            return True
        return False

    def check_word_layout(self, new_layout, inserted_layout, passed_layouts):
        """Check if a word can be layout"""

        new_rect = new_layout.rect
        left, top, right, bottom = \
            new_rect.left, new_rect.top, new_rect.right, new_rect.bottom
        horizontal = new_layout.horizontal

        # Dangerous rects for new layout
        if horizontal:
            danger_rects = [
                IntRect(left - 1, top + 0, right + 1, bottom + 0),
                IntRect(left + 0, top - 1, right + 0, bottom + 1),
            ]
        else:
            danger_rects = [
                IntRect(left + 0, top - 1, right + 0, bottom + 1),
                IntRect(left - 1, top + 0, right + 1, bottom + 0),
            ]
        # Already layouts' rect CAN NOT intersect with dangerous rects
        for layout in self.word_layouts:
            # Skip current being inserted layout
            if layout is inserted_layout:
                continue
            for danger_rect in danger_rects:
                if layout.rect & danger_rect:
                    if not inserted_layout:
                        return False
                    # Inserted: same direction
                    elif layout.horizontal == horizontal:
                        # Exception:
                        #   Like the following, 'as' should connect with 'saw' in char 'a'
                        #
                        #   was
                        #     a
                        #     w
                        #
                        if not (inserted_layout.can_intersect() and
                                layout.rect & inserted_layout.rect and
                                layout.rect.intersect(danger_rect).area() == 1):
                            return False
                    # Inserted: reversed direction
                    else:
                        # Exception:
                        if not (
                                layout.can_intersect() and
                                # Old layout will intersect new layout with same char
                                new_layout & layout
                        ):
                            return False
                        passed_layouts.add(layout)
        return True

    def layout_word_not_insert(self, word):
        """Layout a word, WITHOUT inserted layout"""

        # Search layout point from center to outside spirally
        for x, y in self.rect:
            if self.check_and_add_word_layout(word, x, y, horizontal=True) or \
                    self.check_and_add_word_layout(word, x, y, horizontal=False):
                return True

        # Clock-wisely layout on the outer 4 sides of words' layouts rect
        positions_array = [
            # 0.same direction:
            #   horizontal layouts horizontally, vertical layouts vertically, connected to rect
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
            # 1.same direction:
            #   horizontal layouts horizontally, vertical layouts vertically, NOT connected to rect
            [
                (self.rect.left, self.rect.top - 2, True),
                (self.rect.right + 1, self.rect.top, False),
                (self.rect.left, self.rect.bottom + 1, True),
                (self.rect.left - 2, self.rect.top, False),
            ],
            # 2.reversed direction:
            #   horizontal layouts vertically, vertical layouts horizontally, NOT connected to rect
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
        """Layout a word if it is insert-able"""

        # Find each same char and indexes between new word and each one of already layout words
        for layout in self.word_layouts:

            layout_word = layout.word
            horizontal = layout.horizontal
            left, top = layout.rect.left, layout.rect.top

            for char_index, char in enumerate(word):
                for layout_char_index, layout_char in enumerate(layout_word):
                    if char == layout_char:
                        # Set insertion point base on both indexes
                        x, y = (left + layout_char_index, top - char_index) if horizontal \
                            else (left - char_index, top + layout_char_index)
                        if self.check_and_add_word_layout(
                                word, x, y, not horizontal, inserted_layout=layout):
                            return True
        return False

    def do_layout(self):
        """Layout words"""

        # First word layout at (0, 0), vertically if width not enough
        assert self.check_and_add_word_layout(
            self.words[0], x=0, y=0,
            horizontal=self._real_rect_max_width >= len(self.words[0])
        )

        left_words = self.words[1:]
        while len(left_words) > len(self.words) - self.layout_count:
            # Find and layout a insert-able word in words
            for word in left_words:
                if self.layout_word(word):
                    left_words.remove(word)
                    break
            # Can't find
            else:
                # Layout word, WITHOUT inserted layout
                self.layout_word_not_insert(left_words[0])
                left_words.remove(left_words[0])
            # Layout next

    def print_layout(self, word_rewrite_callback=lambda word: word, prior_words=()):
        """Print layout"""
        board_margin = 2
        board_width = self.rect.width + 2 * board_margin
        board_height = self.rect.height + 2 * board_margin
        board = [list(" " * board_width) for _ in range(board_height)]

        # Print borders
        for y in range(board_height):
            board[y][0] = board[y][-1] = "|"
        for x in range(board_width):
            board[0][x] = board[-1][x] = "-"
        board[0][0] = \
            board[-1][0] = \
            board[0][-1] = \
            board[-1][-1] = "+"

        # Print width/height at top-right/bottom-left
        board[0][-len(str(self.rect.width)):] = str(self.rect.width)
        board[-1][:len(str(self.rect.height))] = str(self.rect.height)

        # Print unfinished words first with '*'
        words = list(prior_words)
        words += [word for word in self.layout_words() if word not in words]
        word_layouts_dict = {
            layout.word: layout for layout in self.word_layouts
        }
        for word in words:
            layout = word_layouts_dict[word]
            # Convert coordinate to 2D array
            board_x = layout.rect.left - self.rect.left + board_margin
            board_y = layout.rect.top - self.rect.top + board_margin
            layout.print_layout(board, board_x, board_y, word_rewrite_callback)

        print("\n".join("".join(_) for _ in board))


if __name__ == "__main__":
    from collections import namedtuple
    import time

    Level = namedtuple(
        "Level",
        [
            "level",
            "count",
            "seed_word",
            "other_words",
        ]
    )

    levels = []
    # Levels initialize
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
