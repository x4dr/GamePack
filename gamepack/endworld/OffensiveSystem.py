from typing import Dict, Any, List

from gamepack.endworld.System import System


class OffensiveSystem(System):
    headers = [
        "Energy",
        "Mass",
        "Damage",
        "Range",
        "Ammo",
        "Heat",
        "Boot",
        "Modes",
        "Amount",
        "Enabled",
    ]
    systype = "offensive"

    damage: float
    weapon_range: str
    ammo: str
    modes: str
    weapon_type: str

    def __init__(self, name: str, data: Dict[str, Any]):
        super().__init__(name, data)
        self.damage = self.number(self.extract("damage"))
        self.weapon_range = str(self.extract("range", "-"))
        self.ammo = str(self.extract("ammo", "-"))
        self.modes = str(self.extract("modes", "-"))
        self.weapon_type = str(self.extract("type", "Ballistic"))

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            "Damage": f"{self.damage:g}",
            "Range": self.weapon_range,
            "Ammo": self.ammo,
            "Boot": str(self.activation_rounds),
            "Modes": self.modes,
            "Type": self.weapon_type,
        }

    def get_headers(self) -> List[str]:
        bonusheaders = []
        for h in self._data.keys():
            if h.title() not in self.headers:
                bonusheaders.append(h.title())
        return self.headers + bonusheaders
