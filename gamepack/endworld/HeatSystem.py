from gamepack.endworld.System import System


@System.register("Heat")
class HeatSystem(System):
    headers = ["Capacity", "Passive", "Active", "Flux", "Current"]

    def __init__(self, name, data):
        super().__init__(name, data)
        self.capacity = self.number(self.extract("capacity"))
        self.passive = self.extract("passive")
        self.active = self.extract("active")
        self.flux = self.number(self.extract("flux"))
        self.current = self.number(self.extract("current"))

    def accept(self, heat):
        if self.current + heat <= self.capacity:
            self.current += heat
            return True
        return False

    def cool(self, powered=False):
        def unpack(inp: str):
            r, a = 0, 0
            for part in inp.split("+"):
                if part := part.strip():
                    if part.endswith("%"):
                        r += self.number(part)
                    else:
                        a += self.number(part)
            return r, a

        relative, absolute = unpack(self.passive)
        if powered:
            active_r, active_a = unpack(self.active)
            relative += active_r
            absolute += active_a
        self.current -= self.current * relative
        self.current -= absolute
        self.current = int(max(self.current, 0))  # round down and clamp to 0

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            "Capacity": self.capacity,
            "Passive": self.passive,
            "Active": self.active,
            "Flux": self.flux,
            "Current": self.current,
        }
