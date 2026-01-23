import unittest
from unittest.mock import patch, MagicMock
from gamepack.endworld.EWCharacter import EWCharacter
from gamepack.MDPack import MDObj


class TestEWCharacter(unittest.TestCase):
    def test_init(self):
        char = EWCharacter()
        self.assertIsNone(char.mecha)

    @patch("gamepack.endworld.Mecha.Mecha.from_mdobj")
    @patch("gamepack.WikiPage.WikiPage.locate")
    @patch("gamepack.WikiPage.WikiPage.load")
    def test_from_mdobj_with_mech_link(
        self, mock_load, mock_locate, mock_mecha_from_md
    ):
        md_text = "# Mech\n(SomeMechLink)"
        mdobj = MDObj.from_md(md_text)

        mock_locate.return_value = "path/to/mech.md"
        mock_page = MagicMock()
        mock_load.return_value = mock_page
        mock_page.md.return_value = MDObj.from_md("# Mecha Section")

        mock_mecha = MagicMock()
        mock_mecha_from_md.return_value = mock_mecha

        char = EWCharacter.from_mdobj(mdobj)
        self.assertEqual(char.mecha, mock_mecha)
        mock_locate.assert_called_with("SomeMechLink")

    @patch("gamepack.endworld.Mecha.Mecha.from_mdobj")
    def test_from_mdobj_with_inline_systems(self, mock_mecha_from_md):
        md_text = "# Mech\n## Systems\nSystem content"
        mdobj = MDObj.from_md(md_text)

        mock_mecha = MagicMock()
        mock_mecha_from_md.return_value = mock_mecha

        char = EWCharacter.from_mdobj(mdobj)
        self.assertEqual(char.mecha, mock_mecha)
        # Should call from_mdobj with the "Mech" section which has "Systems" child
        self.assertTrue(mock_mecha_from_md.called)


if __name__ == "__main__":
    unittest.main()
