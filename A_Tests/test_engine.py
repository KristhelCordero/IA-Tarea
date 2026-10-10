import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from game import action, createBoard, isBoardFull, isWin


class GameEngineUnitTests(unittest.TestCase):
    def test_merges_two_adjacent_tiles_of_same_color(self):
        board = createBoard(2)
        board[0][0] = (1, 2)

        action((1, 3), (0, 1), board)

        self.assertEqual(board[0][0], (0, 0))
        self.assertEqual(board[0][1], (1, 5))

    def test_merges_component_of_three_or_more_tiles(self):
        board = createBoard(3)
        board[0][1] = (2, 2)
        board[1][0] = (2, 3)
        board[1][2] = (2, 4)

        action((2, 5), (1, 1), board)

        self.assertEqual(board[1][1], (2, 14))
        self.assertEqual(board[0][1], (0, 0))
        self.assertEqual(board[1][0], (0, 0))
        self.assertEqual(board[1][2], (0, 0))

    def test_places_tile_without_merging(self):
        board = createBoard(2)
        board[0][0] = (1, 7)

        action((2, 4), (0, 1), board)

        self.assertEqual(board[0][0], (1, 7))
        self.assertEqual(board[0][1], (2, 4))
        self.assertEqual(board[1][0], (0, 0))
        self.assertEqual(board[1][1], (0, 0))

    def test_full_board_with_remaining_tiles_is_a_loss(self):
        board = [[(1, 2), (2, 3)], [(2, 4), (1, 5)]]
        remaining_tiles = [(1, 6)]

        self.assertTrue(isBoardFull(board))
        self.assertFalse(isWin(remaining_tiles))


if __name__ == "__main__":
    unittest.main()