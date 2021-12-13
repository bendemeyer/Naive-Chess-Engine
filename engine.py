from __future__ import annotations

import math

from collections import defaultdict
from operator import itemgetter
from typing import Dict, Generator, List, Optional, Set, Tuple

from board import Board, EmptyMove, Move
from pieces import Color


class Suggestion(object):
    def __init__(self, score: float, move: Move):
        self.score: float = score
        self.move: Move = move


class MoveNode(object):
    def __init__(self, board: Board, parent: Optional[MoveNode] = None):
        self.board: Board = board
        self.parent: Optional[MoveNode] = parent
        self.move_number = 0 if parent is None else parent.move_number + 1
        self._reset_children()
        self.leaf_nodes.add(self)
        if self.parent is not None:
            self.parent.update_child_size(self)
            self.parent.update_child_leaves(self)

    def _reset_children(self):
        self.children: Dict[Move, MoveNode] = {}
        self.size = 1
        self._child_sizes: Dict[Move, int] = defaultdict(int)
        self.score: float = self.board.state.material
        self.sorted_child_scores: List[Tuple[float, Move]] = []
        self.leaf_nodes: Set[MoveNode] = set()
        self._child_leaves: Dict[Move, Set[MoveNode]] = defaultdict(set)
        self.is_checkmate: bool = False
        self.is_stalemate: bool = False

    def prepare_children(self):
        self._reset_children()
        try:
            for board in self.board.generate_legal_moves():
                child = MoveNode(board, self)
                move = board.state.last_move
                self.children[move] = child
        except Exception as e:
            print([(move.start.to_name(), move.end.to_name()) for move in self.get_move_history()])
            raise e
        if not self.children:
            self.leaf_nodes.add(self)
            if self.board.state.check_vectors[self.board.state.turn]:
                self.is_checkmate = True
            else:
                self.is_stalemate = True
        if self.parent is not None:
            self.parent.update_child_size(self)
            self.parent.update_child_leaves(self)

    def get_move_history(self) -> List[Move]:
        if self.parent is not None:
            history = self.parent.get_move_history()
        else:
            history = []
        if not isinstance(self.board.state.last_move, EmptyMove):
            history.append(self.board.state.last_move)
        return history

    def calculate_score(self) -> float:
        color_modifier: int = 1 if self.board.state.turn == Color.WHITE else -1
        if self.is_checkmate:
            score: float = 100 * color_modifier
        elif self.is_stalemate:
            score: float = 0
        elif not self.children:
            score: float = self.board.state.material
        else:
            score: float = 0
            reverse: bool = self.board.state.turn == Color.BLACK
            self.sorted_child_scores: List[Tuple[float, Move]] = sorted(
                [ (c.calculate_score(), c.board.state.last_move) for c in self.children.values() ],
                reverse=reverse, key=itemgetter(0))
            for index, (child_score, move) in enumerate(self.sorted_child_scores):
                multiplier: float = math.pow(0.5, index)
                score = child_score * multiplier
        self.score = score
        return self.score

    def update_child_size(self, child: MoveNode):
        old_size = self._child_sizes[child.board.state.last_move]
        self.size -= old_size
        self.size += child.size
        self._child_sizes[child.board.state.last_move] = child.size
        if self.parent is not None:
            self.parent.update_child_size(self)

    def update_child_leaves(self, child: MoveNode):
        old_leaves = self._child_leaves[child.board.state.last_move]
        self.leaf_nodes.difference_update(old_leaves)
        self.leaf_nodes.update(child.leaf_nodes)
        self._child_leaves[child.board.state.last_move] = child.leaf_nodes
        if self.parent is not None:
            self.parent.update_child_leaves(self)


class Engine(object):
    def __init__(self, start: Board, max_depth: float, max_breadth: float):
        self.root: MoveNode = MoveNode(start)
        self.max_depth: float = max_depth
        self.max_breadth: float = max_breadth
        self.depth: int = 0

    def build_tree(self):
        while self.depth < self.max_depth and self.root.size < self.max_breadth:
            current_leaves: List[MoveNode] = list(self.root.leaf_nodes)
            for leaf in current_leaves:
                leaf.prepare_children()
            self.depth += 1
        self.root.calculate_score()

    def generate_suggestions(self) -> Generator[Suggestion, None, None]:
        for score, move in reversed(self.root.sorted_child_scores):
            yield Suggestion(score, move)

    def get_all_suggestions(self) -> List[Suggestion]:
        return [ Suggestion(score, move) for (score, move) in reversed(self.root.sorted_child_scores) ]

    def make_move(self, move: Move):
        self.root = self.root.children[move]
        self.root.parent = None
        self.depth -= 1
