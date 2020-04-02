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
Misha Schwartz, and Jaisie Sin.

=== Module Description ===

This file contains the hierarchy of player classes.
"""
from __future__ import annotations
from typing import List, Optional, Tuple
import random
import pygame

from block import Block
from goal import Goal, generate_goals

from actions import KEY_ACTION, ROTATE_CLOCKWISE, ROTATE_COUNTER_CLOCKWISE, \
    SWAP_HORIZONTAL, SWAP_VERTICAL, SMASH, PASS, PAINT, COMBINE


def create_players(num_human: int, num_random: int, smart_players: List[int]) \
        -> List[Player]:
    """Return a new list of Player objects.

    <num_human> is the number of human player, <num_random> is the number of
    random players, and <smart_players> is a list of difficulty levels for each
    SmartPlayer that is to be created.

    The list should contain <num_human> HumanPlayer objects first, then
    <num_random> RandomPlayer objects, then the same number of SmartPlayer
    objects as the length of <smart_players>. The difficulty levels in
    <smart_players> should be applied to each SmartPlayer object, in order.
    """
    players = []

    x = 0
    goals = generate_goals(num_human + num_random + len(smart_players))

    for dummy in range(num_human):
        players.append(HumanPlayer(x, goals[x]))
        x += 1

    for dummy in range(num_random):
        players.append(RandomPlayer(x, goals[x]))
        x += 1

    for player in smart_players:
        players.append(SmartPlayer(x, goals[x], player))
        x += 1

    return players


def _get_block(block: Block, location: Tuple[int, int], level: int) -> \
        Optional[Block]:
    """Return the Block within <block> that is at <level> and includes
    <location>. <location> is a coordinate-pair (x, y).

    A block includes all locations that are strictly inside of it, as well as
    locations on the top and left edges. A block does not include locations that
    are on the bottom or right edge.

    If a Block includes <location>, then so do its ancestors. <level> specifies
    which of these blocks to return. If <level> is greater than the level of
    the deepest block that includes <location>, then return that deepest block.

    If no Block can be found at <location>, return None.

    Preconditions:
        - 0 <= level <= max_depth

    """
    x, y = location

    if x >= block.position[0] + block.size or \
            y >= block.position[1] + block.size:
        # no block can be found at location
        return None

    else:  # block/leaf can be found at location
        if level == block.level or block.max_depth == block.level or \
                block.children == []:
            return block

        current = block.children[0]
        for child in block.children:  # find child at location
            child_x, child_y = child.position
            if child_x <= x < child_x + child.size and \
                    child_y <= y < child_y + child.size:
                current = child

        if current.level < level and current.max_depth > current.level:
            # recurse through child if level is bigger
            current = _get_block(current, location, level)

        return current


def _find_random_block(board: Block) -> Block:
    """Find a random block where the
    board.level <= block.level <= depth
    if block the block does not have children, return that block

    """
    depth = random.randint(0, board.max_depth)
    position = board.position
    size = board.size - 1

    x_random = random.randint(position[0], position[0] + size)
    y_random = random.randint(position[1], position[1] + size)

    block = _get_block(board, (x_random, y_random), depth)
    return block


def _valid_moves(board: Block, colour: Tuple[int, int, int]) -> \
        List[Tuple[str, Optional[int], Block]]:
    """Return the list of valid moves.  PASS is always included at the end.

    The move is a tuple consisting of a string, an optional integer, and
    a block. The string indicates the move being made. The integer indicates
    the direction. And the block indicates which block is being acted on.

    <colour> is the goal colour to check if PAINT action is valid.
    """

    output = list()

    # The main gimmick is that if you attempt an impossible move,
    # nothing is changed
    # But if you can, just simply invert the operation
    # Better design would be to have a <swappable> or <paintable>

    if board.smashable():
        # <smash> is valid
        output.append(_create_move(SMASH, board))  # safe to use <board>??

    if board.children != [] and board.colour is None:
        # <swap> is valid
        output.append(_create_move(SWAP_HORIZONTAL, board))
        output.append(_create_move(SWAP_VERTICAL, board))

    if board.children != [] and board.colour is None:
        # <rotate> is valid
        output.append(_create_move(ROTATE_CLOCKWISE, board))
        output.append(_create_move(ROTATE_COUNTER_CLOCKWISE, board))

    # Painted twice, because if block is has colour (0, 0, 0) then
    # it doesnt have colour (0, 0, 1).  So one of those colours are distinct
    if board.max_depth == board.level and board.colour != colour:
        # <paint> is valid
        output.append(_create_move(PAINT, board))

    # This is the only non-invertible function.  Do it last
    if board.level == board.max_depth - 1 and board.children != []:
        # <combine> is valid
        output.append(_create_move(COMBINE, board))

    return output


class Player:
    """A player in the Blocky game.

    This is an abstract class. Only child classes should be instantiated.

    === Public Attributes ===
    id:
        This player's number.
    goal:
        This player's assigned goal for the game.
    """
    id: int
    goal: Goal

    def __init__(self, player_id: int, goal: Goal) -> None:
        """Initialize this Player.
        """
        self.goal = goal
        self.id = player_id

    def get_selected_block(self, board: Block) -> Optional[Block]:
        """Return the block that is currently selected by the player.

        If no block is selected by the player, return None.
        """
        raise NotImplementedError

    def process_event(self, event: pygame.event.Event) -> None:
        """Update this player based on the pygame event.
        """
        raise NotImplementedError

    def generate_move(self, board: Block) -> \
            Optional[Tuple[str, Optional[int], Block]]:
        """Return a potential move to make on the game board.

        The move is a tuple consisting of a string, an optional integer, and
        a block. The string indicates the move being made (i.e., rotate, swap,
        or smash). The integer indicates the direction (i.e., for rotate and
        swap). And the block indicates which block is being acted on.

        Return None if no move can be made, yet.
        """
        raise NotImplementedError


def _create_move(action: Tuple[str, Optional[int]], block: Block) -> \
        Tuple[str, Optional[int], Block]:
    return action[0], action[1], block


class HumanPlayer(Player):
    """A human player.
    """
    # === Private Attributes ===
    # _level:
    #     The level of the Block that the user selected most recently.
    # _desired_action:
    #     The most recent action that the user is attempting to do.
    #
    # == Representation Invariants concerning the private attributes ==
    #     _level >= 0
    _level: int
    _desired_action: Optional[Tuple[str, Optional[int]]]

    def __init__(self, player_id: int, goal: Goal) -> None:
        """Initialize this HumanPlayer with the given <renderer>, <player_id>
        and <goal>.
        """
        Player.__init__(self, player_id, goal)

        # This HumanPlayer has not yet selected a block, so set _level to 0
        # and _selected_block to None.
        self._level = 0
        self._desired_action = None

    def get_selected_block(self, board: Block) -> Optional[Block]:
        """Return the block that is currently selected by the player based on
        the position of the mouse on the screen and the player's desired level.

        If no block is selected by the player, return None.
        """
        mouse_pos = pygame.mouse.get_pos()
        block = _get_block(board, mouse_pos, self._level)

        return block

    def process_event(self, event: pygame.event.Event) -> None:
        """Respond to the relevant keyboard events made by the player based on
        the mapping in KEY_ACTION, as well as the W and S keys for changing
        the level.
        """
        if event.type == pygame.KEYDOWN:
            if event.key in KEY_ACTION:
                self._desired_action = KEY_ACTION[event.key]
            elif event.key == pygame.K_w:
                self._level = max(0, self._level - 1)
                self._desired_action = None
            elif event.key == pygame.K_s:
                self._level += 1
                self._desired_action = None

    def generate_move(self, board: Block) -> \
            Optional[Tuple[str, Optional[int], Block]]:
        """Return the move that the player would like to perform. The move may
        not be valid.

        Return None if the player is not currently selecting a block.
        """
        block = self.get_selected_block(board)

        if block is None or self._desired_action is None:
            return None
        else:
            move = _create_move(self._desired_action, block)

            self._desired_action = None
            return move


class RandomPlayer(Player):
    """A computer player who makes a random valid move on a random block.
    Random players do not pass.
    === Private Attributes ===
    _proceed: True when the player should make a move,
              False when the player should wait.
    """
    _proceed: bool

    def __init__(self, player_id: int, goal: Goal) -> None:
        super().__init__(player_id, goal)
        self._proceed = False

    def get_selected_block(self, board: Block) -> Optional[Block]:
        return None

    def process_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._proceed = True

    def generate_move(self, board: Block) ->\
            Optional[Tuple[str, Optional[int], Block]]:
        """Return a valid, randomly generated move.

        A valid move is a move other than PASS that can be successfully
        performed on the <board>.

        This function does not mutate <board>.
        """
        if not self._proceed:
            return None  # Do not remove

        self._proceed = False  # Must set to False before returning!
        colour = self.goal.colour

        if board.max_depth == board.level:  # block is the max depth
            valid_list = _valid_moves(board, colour)
            if len(valid_list) == 0:  # no valid moves
                return self.generate_move(board)
            random_index = random.randint(0, len(valid_list) - 1)
            return valid_list[random_index]

        # find random block at random depth
        block = _find_random_block(board)

        # generate valid moves on that random block
        copy = block.create_copy()
        valid_list = _valid_moves(copy, colour)

        if len(valid_list) == 0:  # no valid moves
            return self.generate_move(board)

        # Make a random selection
        random_index = random.randint(0, len(valid_list) - 1)
        move = valid_list[random_index][0]
        direction = valid_list[random_index][1]
        return move, direction, block


class SmartPlayer(Player):
    """A computer player that chooses moves more intelligently: It generates a
    set of random moves and, for each move, checks what its score would be if
    it were to make that move. Then it picks the one that yields the best score.
    === Private Attributes ===
    _proceed:
      True when the player should make a move, False when the player should
      wait.
    _difficulty:
      A level indicating how difficult the smart player
      is to play against.
    """
    _proceed: bool
    _difficulty: int

    def __init__(self, player_id: int, goal: Goal, difficulty: int) -> None:
        super().__init__(player_id, goal)
        self._difficulty = difficulty
        self._proceed = False

    def get_selected_block(self, board: Block) -> Optional[Block]:
        return None

    def process_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._proceed = True

    def generate_move(self, board: Block) ->\
            Optional[Tuple[str, Optional[int], Block]]:
        """Return a valid move by assessing multiple valid moves and choosing
        the move that results in the highest score for this player's goal (i.e.,
        disregarding penalties).

        A valid move is a move other than PASS that can be successfully
        performed on the <board>. If no move can be found that is better than
        the current score, this player will pass.

        This function does not mutate <board>.
        """
        if not self._proceed:
            return None  # Do not remove

        self._proceed = False  # Must set to False before returning!

        main_copy = board.create_copy()

        moves = self._valid_move_list(main_copy, self._difficulty)

        if moves == []:
            return _create_move(PASS, board)

        x = self._calculate_best_move(board, moves)

        # find the block corresponding to the <board>
        block_being_moved = _get_block(board, x[2].position,
                                       x[2].level)

        if x[0] == 'pass':
            return _create_move(PASS, board)

        return x[0], x[1], block_being_moved

    def _calculate_best_move(self, board: Block,
                             moves: List[Tuple[str, Optional[int], Block]]) \
            -> [Tuple[str, Optional[int], Block]]:
        """Return the best move that would result in the highest score
        disregarding penalties on the board.

        The method does not mutate <board>.
        """
        best_score = self.goal.score(board)
        best_move = ('pass', None)
        current_block = board

        for move in moves:
            main_copy = board.create_copy()
            block_being_moved = _get_block(main_copy, move[2].position,
                                           move[2].level)

            if move[0] == 'swap' and move[1] == 0:
                block_being_moved.swap(0)

            elif move[0] == 'swap' and move[1] == 1:
                block_being_moved.swap(1)

            elif move[0] == 'combine':
                block_being_moved.combine()

            elif move[0] == 'paint':
                block_being_moved.paint(self.goal.colour)

            elif move[0] == 'rotate' and move[1] == 1:
                block_being_moved.rotate(1)

            elif move[0] == 'rotate' and move[1] == 3:
                block_being_moved.rotate(3)

            elif move[0] == 'smash':
                block_being_moved.smash()

            cur_score = self.goal.score(main_copy)
            if cur_score > best_score:
                best_score = cur_score
                best_move = (move[0], move[1])
                current_block = move[2]

        return _create_move(best_move, current_block)

    def _valid_move_list(self, board: Block, difficulty: int) -> \
            List[Tuple[str, Optional[int], Block]]:
        """Return a list of length n valid moves on some random blocks
        in the <board>.
        """

        moves = []
        colour = self.goal.colour

        for dummy in range(difficulty):
            # find random block, the moves do not need to be unique
            block = _find_random_block(board)
            moves.extend(_valid_moves(block, colour))
        if len(moves) > difficulty:
            moves = random.sample(moves, difficulty)
        return moves


if __name__ == '__main__':
    import python_ta

    python_ta.check_all(config={
        'allowed-io': ['process_event'],
        'allowed-import-modules': [
            'doctest', 'python_ta', 'random', 'typing', 'actions', 'block',
            'goal', 'pygame', '__future__'
        ],
        'max-attributes': 10,
        'generated-members': 'pygame.*'
    })
