"""CSC148 Assignment 2

=== CSC148 Winter 2020 ===
Department of Computer Science,
University of Toronto

This code is provided solely for the personal and private use of
students taking the CSC148 course at the University of Toronto.
Copying for purposes other than this use is expressly prohibited.
All forms of distribution of this code, whether as given or with
any changes, are expressly prohibited.

Authors: Diane Horton, David Liu, Mario Badr, Sophia Huynh, Misha Schwartz,
and Jaisie Sin

All of the files in this directory and all subdirectories are:
Copyright (c) Diane Horton, David Liu, Mario Badr, Sophia Huynh,
Misha Schwartz, and Jaisie Sin

=== Module Description ===

This file contains the hierarchy of Goal classes.
"""
from __future__ import annotations
import random
from typing import List, Tuple
from block import Block
from settings import colour_name, COLOUR_LIST


def generate_goals(num_goals: int) -> List[Goal]:
    """Return a randomly generated list of goals with length num_goals.

    All elements of the list must be the same type of goal, but each goal
    must have a different randomly generated colour from COLOUR_LIST. No two
    goals can have the same colour.

    Precondition:
        - num_goals <= len(COLOUR_LIST)
    """
    x = random.randint(0, 1)
    lst = []
    unused_colours = COLOUR_LIST.copy()
    if x == 0:
        for dummy in range(num_goals):
            random_colour = random.choice(unused_colours)
            unused_colours.remove(random_colour)
            lst.append(BlobGoal(random_colour))
    else:
        for dummy in range(num_goals):
            random_colour = random.choice(unused_colours)
            unused_colours.remove(random_colour)
            lst.append(PerimeterGoal(random_colour))

    return lst


def _flatten(block: Block) -> List[List[Tuple[int, int, int]]]:
    """Return a two-dimensional list representing <block> as rows and columns of
    unit cells.

    Return a list of lists L, where,
    for 0 <= i, j < 2^{max_depth - self.level}
        - L[i] represents column i and
        - L[i][j] represents the unit cell at column i and row j.

    Each unit cell is represented by a tuple of 3 ints, which is the colour
    of the block at the cell location[i][j]

    L[0][0] represents the unit cell in the upper left corner of the Block.
    """
    # <block> is a unit block
    if block.level == block.max_depth:
        return [[(block.colour)]]

    # <block> is not sub divided
    if block.smashable():
        copy = block.create_copy()

        # create children
        children_size = round(block.size / 2.0)
        x = block.position[0]
        y = block.position[1]
        locations = [(x + children_size, y), (x, y), (x, y + children_size),
                     (x + children_size, y + children_size)]

        top_right = Block(locations[0], children_size, copy.colour,
                          copy.level + 1, copy.max_depth)
        top_left = Block(locations[1], children_size, copy.colour,
                         copy.level + 1, copy.max_depth)
        bot_left = Block(locations[2], children_size, copy.colour,
                         copy.level + 1, copy.max_depth)
        bot_right = Block(locations[3], children_size, copy.colour,
                          copy.level + 1, copy.max_depth)

        copy.children.extend([top_right, top_left, bot_left, bot_right])
        copy.colour = None
        return _flatten(copy)

    # Recursive Case
    length = 2 ** (block.max_depth - block.level)
    diff = int(length / 2)
    output = list()

    top_right = _flatten(block.children[0])
    top_left = _flatten(block.children[1])
    bot_left = _flatten(block.children[2])
    bot_right = _flatten(block.children[3])

    # Allocate Memory
    for c in range(length):
        output.append(list())
        for r in range(length):
            output[c].append(list())

    for c in range(diff):
        for r in range(diff):
            # Distribute
            output[c][r] = top_left[c][r]  # Insert <top_left>
            output[c + diff][r] = top_right[c][r]  # Insert <top_right>
            output[c][r + diff] = bot_left[c][r]  # Insert <bot_left>
            output[c + diff][r + diff] = bot_right[c][r]  # Insert <bot_right>

    return output


class Goal:
    """A player goal in the game of Blocky.

    This is an abstract class. Only child classes should be instantiated.

    === Attributes ===
    colour:
        The target colour for this goal, that is the colour to which
        this goal applies.
    """
    colour: Tuple[int, int, int]

    def __init__(self, target_colour: Tuple[int, int, int]) -> None:
        """Initialize this goal to have the given target colour.
        """
        self.colour = target_colour

    def score(self, board: Block) -> int:
        """Return the current score for this goal on the given board.

        The score is always greater than or equal to 0.
        """
        raise NotImplementedError

    def description(self) -> str:
        """Return a description of this goal.
        """
        raise NotImplementedError


class PerimeterGoal(Goal):
    """A goal of getting the largest number of unit cells of the goal colour
    on the perimeter. Corner units count twice towards the score.
    """
    def score(self, board: Block) -> int:
        count = 0
        game = _flatten(board)
        for i in range(len(game)):
            # Top Row
            if game[i][0] == self.colour:
                count += 1
            # Bottom Row
            if game[i][len(game) - 1] == self.colour:
                count += 1
            # Left Column
            if game[0][i] == self.colour:
                count += 1
            # Right Column
            if game[len(game) - 1][i] == self.colour:
                count += 1
        return count

    def description(self) -> str:
        return 'Most unit cells of ' + \
            colour_name(self.colour) + ' on the perimeter'


class BlobGoal(Goal):
    """A goal of getting the largest blob of the target colour.
    """
    def score(self, board: Block) -> int:
        largest_blob = 0
        iterable = list()

        board = _flatten(board)
        visited = list()
        for col in range(len(board)):
            visited.append(list())
            for row in range(len(board[col])):
                visited[col].append(-1)
                iterable.append((col, row))

        # Search for largest blob
        for col, row in iterable:
            if visited[col][row] == -1:
                cur = self._undiscovered_blob_size((col, row),
                                                   board,
                                                   visited)
                if cur > largest_blob:
                    largest_blob = cur
        return largest_blob

    def _undiscovered_blob_size(self, pos: Tuple[int, int],
                                board: List[List[Tuple[int, int, int]]],
                                visited: List[List[int]]) -> int:
        """Return the size of the largest connected blob that (a) is of this
        Goal's target colour, (b) includes the cell at <pos>, and (c) involves
        only cells that have never been visited.

        If <pos> is out of bounds for <board>, return 0.

        <board> is the flattened board on which to search for the blob.
        <visited> is a parallel structure that, in each cell, contains:
            -1 if this cell has never been visited
            0  if this cell has been visited and discovered
               not to be of the target colour
            1  if this cell has been visited and discovered
               to be of the target colour

        Update <visited> so that all cells that are visited are marked with
        either 0 or 1.
        """
        # Code Outline:
        # 1) Mark Current Tile on <visited>
        # 2a) If Current Tile is incorrect colour
        # 3a) Exit Immediately
        # 2b) Current Tile is desired colour
        # 3a) Recursively Call on Adjacent Tiles

        # <pos> is out of board bounds
        if pos[0] < 0 or pos[1] < 0 or \
                pos[0] >= len(board) or pos[1] > len(board):
            return 0
        if board[pos[0]][pos[1]] == self.colour:
            # Current Tile is Correct Colour
            visited[pos[0]][pos[1]] = 1
            blob_size = 1
        else:
            # Incorrect Colour
            visited[pos[0]][pos[1]] = 0
            return 0
        # Recursive Calls
        # Sequencing is Up -> Right -> Down -> Left
        cardinals = [(pos[0], pos[1] - 1),  # Up
                     (pos[0] + 1, pos[1]),  # Right
                     (pos[0], pos[1] + 1),  # Down
                     (pos[0] - 1, pos[1])]  # Left

        for (x, y) in cardinals:
            try:
                if visited[x][y] == -1:  # IndexError should throw here
                    # (x, y) not visited
                    blob_size += \
                        self._undiscovered_blob_size((x, y), board, visited)
            except IndexError:
                # We selected and (x, y) out of bounds
                pass  # Do Nothing

        return blob_size

    def description(self) -> str:
        return 'Create a largest “blob” of ' + colour_name(self.colour)


if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={
        'allowed-import-modules': [
            'doctest', 'python_ta', 'random', 'typing', 'block', 'settings',
            'math', '__future__'
        ],
        'max-attributes': 15
    })
