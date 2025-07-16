from gamepack.endworld.System import System


@System.register("Energy")
class EnergySystem(System):
    headers = ["Energy", "Mass", "Amount", "Enabled"]
    enablers = ["x", "t", "y", "1"]

    def __init__(self, name, data):
        super().__init__(name, data)
        self.enabled = self.extract("enabled")

    def provide(self) -> float:
        if any(x in self.enabled for x in self.enablers):
            return self.energy * self.amount
        return 0
