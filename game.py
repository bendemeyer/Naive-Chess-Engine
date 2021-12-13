from __future__ import annotations

import math

from typing import Dict, List, Optional, Set

from board import Board, BoardState, CheckVectors, EmptyMove, GamePiece, Move, Square
from engine import Engine, Suggestion
from pieces import Bishop, Color, King, Knight, Pawn, Piece, Queen, Rook


class GameStatus(object):
    def __init__(self, turn: Color, checks: Dict[Color, CheckVectors], material: int, score: float):
        self.turn: Color = turn
        self.checks: Dict[Color, CheckVectors] = checks
        self.material: int = material
        self.score: float = score


class Game(object):
    def __init__(self, max_depth: float = math.inf, max_breadth: float = math.inf):
        if max_depth is math.inf and max_breadth is math.inf:
            raise ValueError("At least one of max depth or max breadth must be provided")
        board = Board(self.generate_starting_position(), BoardState(EmptyMove()))
        board.rebuild()
        self.engine: Engine = Engine(board, max_depth, max_breadth)
        self.engine.build_tree()
        self.history: List[Move] = []

    def suggest_moves(self, moves: int = 1) -> List[Suggestion]:
        result: List[Suggestion] = []
        for index, suggestion in enumerate(self.engine.generate_suggestions()):
            if index >= moves:
                break
            result.append(suggestion)
        return result

    def get_all_moves(self) -> List[Suggestion]:
        return self.engine.get_all_suggestions()

    def get_status(self) -> GameStatus:
        return GameStatus(
            self.engine.root.board.state.turn,
            self.engine.root.board.state.check_vectors,
            self.engine.root.board.state.material,
            self.engine.root.score
        )

    def make_move(self, move: Move):
        self.engine.make_move(move)
        self.engine.build_tree()
        self.history.append(move)

    def get_board(self) -> Board:
        return self.engine.root.board

    def piece_at(self, square: Square) -> Optional[Piece]:
        try:
            return self.engine.root.board._position[square].piece
        except KeyError as e:
            return None

    @staticmethod
    def generate_starting_position() -> Dict[Square, GamePiece]:
        return {
            Square.from_name('a1'): GamePiece(Rook(Color.WHITE), Square.from_name('a1')),
            Square.from_name('b1'): GamePiece(Knight(Color.WHITE), Square.from_name('b1')),
            Square.from_name('c1'): GamePiece(Bishop(Color.WHITE), Square.from_name('c1')),
            Square.from_name('d1'): GamePiece(Queen(Color.WHITE), Square.from_name('d1')),
            Square.from_name('e1'): GamePiece(King(Color.WHITE), Square.from_name('e1')),
            Square.from_name('f1'): GamePiece(Bishop(Color.WHITE), Square.from_name('f1')),
            Square.from_name('g1'): GamePiece(Knight(Color.WHITE), Square.from_name('g1')),
            Square.from_name('h1'): GamePiece(Rook(Color.WHITE), Square.from_name('h1')),
            Square.from_name('a2'): GamePiece(Pawn(Color.WHITE), Square.from_name('a2')),
            Square.from_name('b2'): GamePiece(Pawn(Color.WHITE), Square.from_name('b2')),
            Square.from_name('c2'): GamePiece(Pawn(Color.WHITE), Square.from_name('c2')),
            Square.from_name('d2'): GamePiece(Pawn(Color.WHITE), Square.from_name('d2')),
            Square.from_name('e2'): GamePiece(Pawn(Color.WHITE), Square.from_name('e2')),
            Square.from_name('f2'): GamePiece(Pawn(Color.WHITE), Square.from_name('f2')),
            Square.from_name('g2'): GamePiece(Pawn(Color.WHITE), Square.from_name('g2')),
            Square.from_name('h2'): GamePiece(Pawn(Color.WHITE), Square.from_name('h2')),
            Square.from_name('a7'): GamePiece(Pawn(Color.BLACK), Square.from_name('a7')),
            Square.from_name('b7'): GamePiece(Pawn(Color.BLACK), Square.from_name('b7')),
            Square.from_name('c7'): GamePiece(Pawn(Color.BLACK), Square.from_name('c7')),
            Square.from_name('d7'): GamePiece(Pawn(Color.BLACK), Square.from_name('d7')),
            Square.from_name('e7'): GamePiece(Pawn(Color.BLACK), Square.from_name('e7')),
            Square.from_name('f7'): GamePiece(Pawn(Color.BLACK), Square.from_name('f7')),
            Square.from_name('g7'): GamePiece(Pawn(Color.BLACK), Square.from_name('g7')),
            Square.from_name('h7'): GamePiece(Pawn(Color.BLACK), Square.from_name('h7')),
            Square.from_name('a8'): GamePiece(Rook(Color.BLACK), Square.from_name('a8')),
            Square.from_name('b8'): GamePiece(Knight(Color.BLACK), Square.from_name('b8')),
            Square.from_name('c8'): GamePiece(Bishop(Color.BLACK), Square.from_name('c8')),
            Square.from_name('d8'): GamePiece(Queen(Color.BLACK), Square.from_name('d8')),
            Square.from_name('e8'): GamePiece(King(Color.BLACK), Square.from_name('e8')),
            Square.from_name('f8'): GamePiece(Bishop(Color.BLACK), Square.from_name('f8')),
            Square.from_name('g8'): GamePiece(Knight(Color.BLACK), Square.from_name('g8')),
            Square.from_name('h8'): GamePiece(Rook(Color.BLACK), Square.from_name('h8'))
        }
