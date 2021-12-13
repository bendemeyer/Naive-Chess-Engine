from collections import defaultdict
from typing import Dict, List, Tuple
from cmd import Cmd

from board import Move, Square
from engine import MoveNode, Suggestion
from game import Game, GameStatus
from pieces import Color


def format_move(move: Move, game: Game):
    piece = game.piece_at(move.start)
    if piece is None:
        raise ValueError
    piece_name = piece.type.value
    capture = game.piece_at(move.end)
    verb = "to" if capture is None else "takes on"
    return "{piece} on {origin} {verb} {dest}".format(piece=piece_name, origin=move.start.to_name(), verb=verb, dest=move.end.to_name())


def format_suggestion(game: Game, suggestion: Suggestion):
    move_description = format_move(suggestion.move, game)
    return "{desctiption}: {score}".format(desctiption=move_description, score=format(suggestion.score, ".2f"))


def print_status(status: GameStatus):
    print("{color} to move".format(color=status.turn.value))
    for color, vectors in status.checks.items():
        if vectors:
            print("{color} in check".format(color=color.value))
    if status.material == 0:
        print("No material advantage for either side")
    else:
        material_favorite = Color.WHITE.value if status.material > 0 else Color.BLACK.value
        print("Material advantage of {number} favoring {color}".format(number=abs(status.material), color=material_favorite))
    if status.score == 0:
        print("No engine scored advantage for either side")
    else:
        engine_favorite = Color.WHITE.value if status.score > 0 else Color.BLACK.value
        print("Engine scored advantage of {score} favoring {color}".format(score=format(abs(status.score), ".2f"), color=engine_favorite))


class GamePrompt(Cmd):
    prompt = "chess > "

    def __init__(self) -> None:
        super().__init__()
        self.active = True
        self.confirmations = { "yes", "y" }
        max_depth = float(input("Max depth: "))
        max_breadth = float(input("Max breadth: "))
        self.game: Game = Game(max_depth, max_breadth)
        print("New game started!")
        print()

    def do_new(self, args):
        if isinstance(self.game, Game):
            confirm: str = input("Are you sure you want to start a new game? Your current game will be lost! (y/N): ")
            if confirm.lower() not in self.confirmations:
                print("OK, not starting a new game!")
                print()
                return
        print("Starting a new game...")
        max_depth = float(input("Max depth?"))
        max_breadth = float(input("Max breadth?"))
        self.game = Game(max_depth, max_breadth)
        print("New game started!")
        print()

    def do_suggest(self, args):
        suggestion_count = 1
        try:
            suggestion_count = int(args)
        except Exception as e:
            pass
        for suggestion in self.game.suggest_moves(suggestion_count):
            print(format_suggestion(self.game, suggestion))
        print()

    def do_status(self, args):
        print_status(self.game.get_status())
        print()

    def do_move(self, args):
        start = input("Which piece would you like to move? Please provide the square name (e.g. \"b2\"): ")
        while not isinstance(start, Square):
            try:
                start = Square.from_name(start)
            except Exception as e:
                start = input("Invalid square name! Please try again: ")
        end = input("Which square should it move to?: ")
        while not isinstance(end, Square):
            try:
                end = Square.from_name(end)
            except Exception as e:
                end = input("Invalid square name! Please try again: ")
        try:
            self.game.make_move(Move(start, end))
            print("Move made!")
        except Exception as e:
            print([(move.start.to_name(), move.end.to_name()) for move in self.game.history])
            print("The provided move was not valid")
            raise e
        print()

    def do_moves(self, args):
        do_count = False
        do_list = False
        do_prompt = False
        if args in {"-c", "--count", "count"}:
            do_count = True
        elif args in {"-l", "--list", "list"}:
            do_list = True
        else:
            do_prompt = True
        if do_prompt:
            confirm = input("Do you want to get a count of possible moves? (y/N): ")
            if confirm in self.confirmations:
                do_count = True
        if do_count:
             print("There are {count} moves available".format(count=len(self.game.engine.root.children)))
        if do_prompt:
            confirm = input("Do you want to get a list of all possible moves? (y/N): ")
            if confirm in self.confirmations:
                do_list = True
        if do_list:
            for node in self.game.engine.root.children.values():
                move = node.board.state.last_move
                print(format_move(move, self.game))
        print()

    def do_tree(self, args):
        print("There are {count} total nodes in the tree".format(count=self.game.engine.root.size))
        confirm = input("Do you want a level-by-level breakdown? (y/N): ")
        if confirm in self.confirmations:
            level_counts: Dict[int, int] = defaultdict(int)
            level_nodes: List[Tuple[int, MoveNode]] = [(1, self.game.engine.root)]
            while level_nodes:
                level, node = level_nodes.pop(0)
                level_counts[level] += len(node.children)
                level_nodes.extend([(level + 1, child) for child in node.children.values()])
            for level in sorted(list(level_counts.keys())):
                print("Evaluation of level {level} contains {count} nodes".format(level=level, count=level_counts[level]))
        print()

    def do_exit(self, args):
        confirm: str = input("Are you sure you want to exit? Your current game will be lost! (y/N): ")
        if confirm not in self.confirmations:
            print("OK, not exiting!")
            print()
        else:
            print("Exiting...")
            print()
            return True


if __name__ == "__main__":
    GamePrompt().cmdloop()
