from unittest import TestCase

from gamepack.fasthelpers import ascii_graph, montecarlo, plot
from gamepack.fengraph import chances


class TestDice(TestCase):
    def setUp(self) -> None:
        pass

    def test_chances(self):
        for i in range(1, 6):
            for j in range(6):
                for x in chances((i, j), 0):
                    self.assertTrue(x)


# a unittest for the above
class TestDiceParser(TestCase):
    def test_ascii_graph(self):
        occurrences = {1: 10, 2: 5, 3: 15, 4: 20, 5: 25, 6: 5}
        mode = 0
        expected_output = (
            "    1 12.50 ################\n"
            "    2  6.25 ########\n"
            "    3 18.75 ########################\n"
            "    4 25.00 ################################\n"
            "    5 31.25 ########################################\n"
            "    6  6.25 ########\n"
        )
        graph, avg, dev = ascii_graph(occurrences, mode)
        self.assertEqual(avg, 3.75)
        self.assertEqual(dev, 1.4361406616345072)
        self.assertEqual(graph, expected_output)

        mode = 1
        expected_output = (
            "    1 12.50 #####\n"
            "    2 18.75 #######\n"
            "    3 37.50 ###############\n"
            "    4 62.50 #########################\n"
            "    5 93.75 #####################################\n"
            "    6 100.00 ########################################\n"
        )
        graph, avg, dev = ascii_graph(occurrences, mode)
        self.assertEqual(graph, expected_output)
        mode = -1
        expected_output = (
            "    1 100.00 ########################################\n"
            "    2 87.50 ###################################\n"
            "    3 81.25 ################################\n"
            "    4 62.50 #########################\n"
            "    5 37.50 ###############\n"
            "    6  6.25 ##\n"
        )
        graph, avg, dev = ascii_graph(occurrences, mode)
        self.assertEqual(avg, 3.75)
        self.assertEqual(dev, 1.4361406616345072)
        self.assertEqual(graph, expected_output)

    def test_monte_carlo(self):
        res = montecarlo("3d10", 1)
        self.assertIn("from", res)
        self.assertIn("#", res)
        self.assertIn("%", res)

    def test_plot(self):
        data = {-2: 2, 0: 1, 2: 6}
        expected_output = (
            "Of the 9 rolls, 6 were successes, 1 were failures and 2 were botches, averaging 0.89\n"
            "The percentages are:\n"
            "+ : 66.667%\n"
            "0 : 11.111%\n"
            "- : 22.222%\n"
            "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++000000000000----------------------\n"
            "-2 :  22.222% ####################\n"
            "-1 :   0.000% \n\n"
            " 0 :  11.111% ##########\n\n"
            " 1 :   0.000% \n"
            " 2 :  66.667% ############################################################\n"
        )
        self.assertEqual(plot(data, showsucc=True, showgraph=True), expected_output)

        expected_output_with_dmgmods = (
            "Of the 9 rolls, 6 were successes, 1 were failures and 2 were botches, averaging 0.89\n"
            "The percentages are:\n"
            "+ : 66.667%\n"
            "0 : 11.111%\n"
            "- : 22.222%\n"
            "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++000000000000----------------------\n"
            "-2 :  22.222% ####################\n"
            "-1 :   0.000% \n\n"
            " 0 :  11.111% ##########\n\n"
            " 1 :   0.000% \n"
            " 2 :  66.667% ############################################################\n"
            "damage modifiers (adjusted):\n"
            "0.0, 1.0\n"
        )

        self.assertEqual(
            plot(data, showsucc=True, showgraph=True, showdmgmods=True),
            expected_output_with_dmgmods,
        )
        data = {-8: 10, -3: 5, -2: 2, 0: 1, 2: 6, 4: 10, 11: 5, 15: 1}
        expected_output_grouped = (
            "Of the 40 rolls, 22 were successes, 1 were failures and 17 were botches, averaging 0.57\n"
            "The percentages are:\n"
            "+ : 55.000%\n"
            "0 : 2.500%\n"
            "- : 42.500%\n"
            "+++++++++++++++++++++++++++++++++++++++++++++++++++++++000------------------------------------------\n"
            "-10--6 :  25.000% ############################################################\n"
            "-5--1 :  17.500% ##########################################\n\n"
            " 0- 4 :  42.500% #############################################################################"
            "#########################\n\n"
            " 5- 9 :   0.000% \n"
            "10-14 :  12.500% ##############################\n"
            "15-19 :   2.500% ######\n"
        )
        self.assertEqual(
            plot(data, showsucc=True, showgraph=True, grouped=5),
            expected_output_grouped,
        )
