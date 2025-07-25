from gamepack.endworld.System import System


@System.register("Energy")
class EnergySystem(System):
    headers = ["Energy", "Mass", "Amount", "Enabled"]
    systype = "energy"

    def __init__(self, name, data):
        super().__init__(name, data)

    def provide(self) -> float:
        if self.is_active():
            return self.energy * self.amount
        return 0

    def to_dict(self) -> dict:
        return {**super().to_dict(), "Enabled": self.enabled}
