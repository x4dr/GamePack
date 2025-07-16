from gamepack.endworld.System import System


@System.register("Seal")
class SealSystem(System):
    headers = ["Level"]

    def __init__(self, name, data):
        defaults = {"mass": 0, "amount": 1, "energy": 0}
        super().__init__(name, {**defaults, **data})
        self.level = self.number(self.extract("level"))

    def to_dict(self) -> dict:
        return {"Level": self.level}

    def get_headers(self):
        bonusheaders = []
        for h in self._data.keys():
            if h.title() not in self.headers + super().headers:
                # don't want the base headers
                bonusheaders.append(h.title())
        return self.headers + bonusheaders
