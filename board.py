from __future__ import annotations

import copy
from math import perm, pi
from os import path
import uuid

from collections import defaultdict
from typing import Dict, Generator, List, Optional, Set, Tuple

from pieces import Color, King, MovementVector, Piece, PieceType


class Square(object):
    _cols: List[str] = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    _rows: List[str] = ['1', '2', '3', '4', '5', '6', '7', '8']

    def __init__(self, col: int, row: int):
        self.col: int = col
        self.row: int = row

    def __hash__(self):
        return hash(self.get_position())

    def __eq__(self, other: Square) -> bool:
        return self.get_position() == other.get_position()

    def is_valid(self) -> bool:
        return self.col >= 0 and self.col < len(self._cols) and self.row >= 0 and self.row < len(self._rows)

    def find_diff(self, end: Square) -> Tuple[int, int]:
        return (end.col - self.col, end.row - self.row)

    def apply_diff(self, cols: int, rows: int) -> Square:
        new_col = self.col + cols
        new_row = self.row + rows
        return Square(new_col, new_row)

    def get_position(self) -> Tuple[str, str]:
        return (self._cols[self.col], self._rows[self.row])

    def to_name(self) -> str:
        return "".join(self.get_position())

    @classmethod
    def from_name(cls, name: str) -> Square:
        if len(name) != 2:
            raise ValueError
        col_name = name[0]
        row_name = name[1]
        if col_name not in cls._cols or row_name not in cls._rows:
            raise ValueError
        return (cls(cls._cols.index(col_name), cls._rows.index(row_name)))


class CandidateMove(object):
    def __init__(self, square: Square, vector: MovementVector):
        self.square: Square = square
        self.vector: MovementVector = vector


class Move(object):
    def __init__(self, start: Square, end: Square):
        self.start: Square = start
        self.end: Square = end

    def __hash__(self):
        return hash((self.start, self.end))

    def __eq__(self, other: Move):
        return self.start == other.start and self.end == other.end


class EmptyMove(Move):
    def __init__(self):
        pass


class GamePiece(object):
    def __init__(self, piece: Piece, square: Square):
        self._uuid = uuid.uuid4()
        self.piece: Piece = piece
        self.square: Square = square
        self.possible_squares: Dict[Square, MovementVector] = {}

    def __hash__(self):
        return hash(self._uuid)

    def __eq__(self, other: GamePiece):
        return self._uuid == other._uuid

    def _generate_moves(self, vector: MovementVector, square: Square) -> Generator[CandidateMove, None, None]:
        distance: int = 1
        new_square = square
        while True:
            if distance > vector.max_distance:
                break
            if not new_square.is_valid():
                break
            self.possible_squares[new_square] = vector
            yield CandidateMove(new_square, vector)
            distance += 1
            new_square = new_square.apply_diff(*vector.direction)

    def initialize_moves(self) -> Generator[Generator[CandidateMove, None, None], None, None]:
        for vector in self.piece.vectors:
            yield self._generate_moves(vector, self.square.apply_diff(*vector.direction))

    def update_moves(self, move: Move) -> Generator[Generator[CandidateMove, None, None], None, None]:
        if move.start in self.possible_squares:
            yield self._generate_moves(self.possible_squares[move.start], move.start)
        if move.end in self.possible_squares:
            yield self._generate_moves(self.possible_squares[move.end], move.end)

    def move(self, square: Square):
        self.square = square
        self.possible_squares = {}
        self.piece.move()


class KingLocations(object):
    def __init__(self, white: Square = Square.from_name("e1"), black: Square =  Square.from_name("e8")):
        self._locations = {
            Color.WHITE: white,
            Color.BLACK: black
        }
    
    def get(self, color: Color) -> Square:
        return self._locations[color]

    def move(self, move: Move) -> KingLocations:
        if move.start not in self._locations.values():
            return self
        else:
            white = move.end if self._locations[Color.WHITE] == move.start else self._locations[Color.WHITE]
            black = move.end if self._locations[Color.BLACK] == move.start else self._locations[Color.BLACK]
            return KingLocations(white, black)


class CheckVectors(object):
    def __init__(self):
        self.vectors: List[List[Square]] = []

    def __bool__(self):
        return bool(self.vectors)

    def add(self, attacker: Square, king: Square, vector: MovementVector):
        if not vector.can_capture:
            raise ValueError
        path: List[Square] = []
        distance: int = 0
        new_square = attacker
        while True:
            path.append(new_square)
            distance += 1
            if distance > vector.max_distance:
                raise ValueError
            new_square = new_square.apply_diff(*vector.direction)
            if not new_square.is_valid():
                raise ValueError
            if new_square == king:
                break
        self.vectors.append(path)

    def blocking_squares(self) -> Set[Square]:
        if len(self.vectors) != 1:
            return set()
        return set(self.vectors[0])


class BoardState(object):
    def __init__(self, last_move: Move, turn: Color = Color.WHITE, material: int = 0,
                     checks: CheckVectors = CheckVectors(), king_squares: KingLocations = KingLocations()):
        self.last_move: Move = last_move
        self.turn: Color = turn
        self.next_turn = Color.WHITE if self.turn == Color.BLACK else Color.BLACK
        self.material: int = material
        self.check_vectors: Dict[Color, CheckVectors] = {
            self.turn: checks,
            self.next_turn: CheckVectors()
        }
        self.king_squares: KingLocations = king_squares

    def take_turn(self):
        last_turn = self.turn
        self.turn = self.next_turn
        self.next_turn = last_turn


class InvalidPositionException(ValueError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class Board(object):
    def __init__(self, position: Dict[Square, GamePiece], state: BoardState,
                     relevant_piece_squares: Dict[Square, Set[GamePiece]] = defaultdict(set),
                     available_moves: Dict[GamePiece, Set[Square]] = defaultdict(set)):
        self.state = state
        self._position: Dict[Square, GamePiece] = position
        self._relevant_piece_squares: Dict[Square, Set[GamePiece]] = relevant_piece_squares
        self._available_moves: Dict[GamePiece, Set[Square]] = available_moves

    def rebuild(self):
        self._relevant_piece_squares = defaultdict(set)
        self._available_moves = defaultdict(set)
        for piece in self._position.values():
            self.prepare_moves(piece)

    def make_child(self, move: Move):
        child = Board(
            copy.copy(self._position),
            BoardState(
                move,
                self.state.turn,
                self.state.material,
                self.state.check_vectors[self.state.turn],
                self.state.king_squares.move(move)
            ),
            defaultdict(set, { s: copy.copy(g) for s, g in self._relevant_piece_squares.items() }),
            defaultdict(set, { g: copy.copy(s) for g, s in self._available_moves.items() })
        )
        child.make_move(move)
        return child

    def make_move(self, move: Move):
        if move.start not in self._position:
            raise ValueError
        moved_piece = copy.deepcopy(self._position[move.start])
        del self._available_moves[moved_piece]
        self._available_moves[moved_piece] = set()
        for square in moved_piece.possible_squares:
            if moved_piece in self._relevant_piece_squares[square]:
                self._relevant_piece_squares[square].discard(moved_piece)
                self._relevant_piece_squares[square].add(moved_piece)
        if moved_piece.piece.color != self.state.turn:
            print("Making move: {0} to move".format(self.state.turn.value))
            print("Making move: {0} {1} on {2} to {3}".format(moved_piece.piece.color.value, moved_piece.piece.type.value, move.start.to_name(), move.end.to_name()))
            raise ValueError
        if move.end in self._position:
            captured_piece = self._position[move.end]
            self.state.material += captured_piece.piece.value * (1 if captured_piece.piece.color == Color.BLACK else -1)
            del self._available_moves[captured_piece]
            for square in captured_piece.possible_squares:
                self._relevant_piece_squares[square].discard(captured_piece)
        moved_piece.move(move.end)
        self._position[move.end] = moved_piece
        del self._position[move.start]
        self.state.take_turn()
        self.prepare_moves(moved_piece)
        for piece in self._relevant_piece_squares[move.start] | self._relevant_piece_squares[move.start]:
            self.prepare_moves(piece, move)

    def prepare_moves(self, piece: GamePiece, move: Optional[Move] = None):
        if move is None:
            vectors = piece.initialize_moves()
        else:
            vectors = piece.update_moves(move)
        for vector in vectors:
            terminated = False
            for candidate in vector:
                if not terminated:
                    self._relevant_piece_squares[candidate.square].add(piece)
                    if candidate.square in self._position:
                        terminated = True
                        held_by: GamePiece = self._position[candidate.square]
                        if held_by.piece.color != piece.piece.color and candidate.vector.can_capture:
                            if held_by.piece.type == PieceType.KING:
                                if held_by.piece.color == self.state.next_turn:
                                    raise InvalidPositionException
                                else:
                                    self.state.check_vectors[held_by.piece.color].add(piece.square, held_by.square, candidate.vector)
                            self._available_moves[piece].add(candidate.square)
                        else:
                            self._available_moves[piece].discard(candidate.square)
                    else:
                        if not candidate.vector.can_only_capture:
                            self._available_moves[piece].add(candidate.square)
                        else:
                            self._available_moves[piece].discard(candidate.square)
                else:
                    self._relevant_piece_squares[candidate.square].discard(piece)
                    self._available_moves[piece].discard(candidate.square)

    def generate_legal_moves(self) -> Generator[Board, None, None]:
        if self.state.check_vectors[self.state.turn]:
            for board in self._generate_legal_moves_from_check():
                yield board
            return
        for piece, squares in [ (p, s) for (p, s) in self._available_moves.items() if p.piece.color == self.state.turn ]:
            for square in squares:
                try:
                    yield self.make_child(Move(piece.square, square))
                except InvalidPositionException as e:
                    continue
                except Exception as e:
                    print("Generating legal move: {0} to move".format(self.state.turn.value))
                    print("Generating legal move: {0} {1} on {2} to {3}".format(piece.piece.color.value, piece.piece.type.value, piece.square.to_name(), square.to_name()))
                    raise e

    def _generate_legal_moves_from_check(self) -> Generator[Board, None, None]:
        possible_moves: Dict[GamePiece, Set[Square]] = defaultdict(set)
        king_square = self.state.king_squares.get(self.state.turn)
        if king_square not in self._position:
            raise ValueError
        king = self._position[king_square]
        for move in self._available_moves[king]:
            try:
                yield self.make_child(Move(king.square, move))
            except InvalidPositionException as e:
                continue
        possible_moves[king] = self._available_moves[king]
        blocking_squares = self.state.check_vectors[self.state.turn].blocking_squares()
        blocking_pieces: Set[GamePiece] = set()
        for square in blocking_squares:
            blocking_pieces.update({ p for p in self._relevant_piece_squares[square] if p.piece.color == self.state.turn })
        for piece in blocking_pieces:
            for move in self._available_moves[piece]:
                if move in blocking_squares:
                    try:
                        yield self.make_child(Move(piece.square, move))
                    except InvalidPositionException as e:
                        continue
