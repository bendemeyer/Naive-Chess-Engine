from __future__ import annotations

import math

from enum import Enum
from typing import List, Tuple


class PieceType(Enum):
    PAWN = "pawn"
    KNIGHT = "knight"
    BISHOP = "bishop"
    ROOK = "rook"
    QUEEN = "queen"
    KING = "king"


class Color(Enum):
    WHITE = "white"
    BLACK = "black"


class MovementVector(object):
    def __init__(self, direction: Tuple[int, int], max_distance: float = math.inf, can_capture: bool = True, can_only_capture: bool = False):
        self.direction = direction
        self.max_distance = max_distance
        self.can_capture = can_capture
        self.can_only_capture = can_only_capture


class Piece():
    value: int = 0
    type: PieceType
    vectors: List[MovementVector] = []

    def __init__(self, color: Color):
        self.color: Color = color
        self.has_moved: bool = False

    def move(self):
        self.has_moved = True

    def serialize(self) -> Tuple[str, str, bool]:
        return (self.type.value, self.color.value, self.has_moved)


class Pawn(Piece):
    value = 1
    type = PieceType.PAWN

    def __init__(self, color: Color):
        super().__init__(color)
        direction = 1 if self.color == Color.WHITE else -1
        self.vectors = [
            MovementVector((0, direction), 2, False),
            MovementVector((1, direction), 1, True, True),
            MovementVector((-1, direction), 1, True, True)
        ]

    def move(self):
        self.vectors[0].max_distance = 1
        return super().move()


class Knight(Piece):
    value = 3
    type = PieceType.KNIGHT
    vectors = [
        MovementVector((1, 2), 1),
        MovementVector((2, 1), 1),
        MovementVector((2, -1), 1),
        MovementVector((1, -2), 1),
        MovementVector((-1, -2), 1),
        MovementVector((-2, -1), 1),
        MovementVector((-2, 1), 1),
        MovementVector((-1, 2), 1)
    ]


class Bishop(Piece):
    value = 3
    type = PieceType.BISHOP
    vectors = [
        MovementVector((1, 1)),
        MovementVector((1, -1)),
        MovementVector((-1, -1)),
        MovementVector((-1, 1))
    ]


class Rook(Piece):
    value = 5
    type = PieceType.ROOK
    vectors = [
        MovementVector((1, 0)),
        MovementVector((0, 1)),
        MovementVector((-1, 0)),
        MovementVector((0, -1))
    ]


class Queen(Piece):
    value = 9
    type = PieceType.QUEEN
    vectors = Rook.vectors + Bishop.vectors


class King(Piece):
    type = PieceType.KING
    vectors = [ MovementVector(m.direction, 1) for m in Queen.vectors ]
