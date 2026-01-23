import unittest
import io
from unittest.mock import patch, MagicMock
from gamepack.fengraph import (
    modify_dmg,
    chances,
    versus,
    fastdata,
    count_sorted_rolls,
    count_lowest_rolls,
)
from gamepack.Dice import DescriptiveError


class TestFengraph(unittest.TestCase):
    def test_modify_dmg_stechen(self):
        # damage_instance <= armor
        dmg = [[0], [5], [0]]
        res = modify_dmg([1], dmg, "Stechen", 10)
        self.assertEqual(res, 0)

        # damage_instance > armor
        dmg = [[0], [12], [0]]
        res = modify_dmg([1], dmg, "Stechen", 10)
        self.assertEqual(res, 6)  # ceil(12/2)

    def test_modify_dmg_schlagen(self):
        dmg = [[0], [10], [0]]
        res = modify_dmg([1], dmg, "Schlagen", 4)
        self.assertEqual(res, 8)  # 10 - 4/2

    def test_modify_dmg_schneiden(self):
        # effective_dmg > 0
        dmg = [[0], [10], [0]]
        res = modify_dmg([1], dmg, "Schneiden", 4)
        # effective = 10 - 4 = 6. 6 + ceil(6/5)*3 = 6 + 2*3 = 12
        self.assertEqual(res, 12)

        # effective_dmg <= 0
        res = modify_dmg([1], dmg, "Schneiden", 10)
        self.assertEqual(res, 0)

    def test_modify_dmg_other(self):
        dmg = [[0], [10], [0]]
        res = modify_dmg([1], dmg, "Other", 4)
        self.assertEqual(res, 6)  # 10 - 4

    def test_modify_dmg_complex(self):
        # damage_instance len > 1
        # effective_dmg = instance[0] - max(0, armor - instance[1])
        dmg = [[0], [10, 5], [0]]
        res = modify_dmg([1], dmg, "Other", 4)
        # 10 - max(0, 4 - 5) = 10 - 0 = 10
        self.assertEqual(res, 10)

        dmg = [[0], [10, 2], [0]]
        res = modify_dmg([1], dmg, "Other", 4)
        # 10 - max(0, 4 - 2) = 10 - 2 = 8
        self.assertEqual(res, 8)

    @patch("gamepack.fengraph.dicecache_db")
    @patch("gamepack.fengraph.freq_dicts", {0: {(1, 2): 1}})
    def test_fastdata_cache_hit(self, mock_db):
        mock_conn = MagicMock()
        mock_db.return_value = mock_conn
        mock_conn.execute.return_value.fetchall.return_value = [(10, 100)]

        res = fastdata((1, 2), 0)
        self.assertEqual(res, {10: 100})

    @patch("gamepack.fengraph.dicecache_db")
    def test_fastdata_invalid_mod(self, mock_db):
        res = fastdata((1, 2), 100)
        self.assertEqual(res, {})

    @patch("gamepack.fengraph.dicecache_db")
    @patch(
        "gamepack.fengraph.freq_dicts",
        {
            0: {(1, 2): 1},
            -5: {},
            -4: {},
            -3: {},
            -2: {},
            -1: {},
            1: {},
            2: {},
            3: {},
            4: {},
            5: {},
        },
    )
    def test_fastdata_cache_update(self, mock_db):
        mock_conn = MagicMock()
        mock_db.return_value = mock_conn
        mock_conn.execute.return_value.fetchall.return_value = []

        with self.assertRaises(DescriptiveError) as cm:
            fastdata((1, 2), 0)
        self.assertIn("Cache Updated", str(cm.exception))
        self.assertTrue(mock_conn.commit.called)

    @patch("gamepack.fengraph.fastdata")
    def test_chances_ascii(self, mock_fast):
        mock_fast.return_value = {10: 1}
        res = chances((1, 2), 0)
        # res should be a tuple from ascii_graph
        self.assertIsInstance(res, tuple)

    @patch("gamepack.fengraph.fastdata")
    def test_chances_plot(self, mock_fast):
        mock_fast.return_value = {10: 1, 11: 2}
        # mode 0
        res0 = chances((1, 2), 0, number_of_quantiles=4, mode=0)
        self.assertIsInstance(res0, io.BytesIO)

        # mode 1
        res1 = chances((1, 2), 0, number_of_quantiles=4, mode=1)
        self.assertIsInstance(res1, io.BytesIO)

        # mode -1
        res_m1 = chances((1, 2), 0, number_of_quantiles=4, mode=-1)
        self.assertIsInstance(res_m1, io.BytesIO)

    def test_chances_no_selectors(self):
        with self.assertRaises(DescriptiveError):
            chances((6, 7), 0)

    @patch("gamepack.fengraph.fastversus")
    def test_versus(self, mock_fv):
        mock_fv.return_value = {0: 1}
        res = versus((1,), (1,))
        self.assertIsInstance(res, tuple)

    def test_count_sorted_rolls(self):
        # 1 die, 2 sides: { (1,): 1, (2,): 1 }
        res = count_sorted_rolls(1, 2)
        self.assertEqual(res, {(1,): 1, (2,): 1})

    def test_count_lowest_rolls(self):
        counts = {(1, 2): 1, (1, 1): 1}
        # select 1 lowest
        res = count_lowest_rolls(counts, -1)
        self.assertEqual(res, {(1,): 2})


if __name__ == "__main__":
    unittest.main()
