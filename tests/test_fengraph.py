from unittest import TestCase

from gamepack.fengraph import chances


class TestDice(TestCase):
    def setUp(self) -> None:
        pass

    def test_chances(self):
        for i in range(1, 6):
            for j in range(6):
                for x in chances((i, j), 0):
                    print(x)


6
