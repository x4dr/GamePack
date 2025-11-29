from gamepack.endworld.System import System


@System.register("Movement")
class MovementSystem(System):
    headers = [
        "Energy",
        "Heat",
        "Thrust",
        "Anchor",
        "Dynamics",
        "Mass",
        "Amount",
        "Enabled",
    ]
    systype = "movement"

    def __init__(self, name, data):
        super().__init__(name, data)
        self.thrust = self.number(self.extract("thrust"))
        self.anchor = self.number(self.extract("anchor"))
        self.dynamics = self.number(self.extract("dynamics"))

    def __repr__(self):
        return (
            f"Movement System {self.name}: "
            f"Thrust={self.thrust}, "
            f"Anchor={self.anchor}, "
            f"Dynamics={self.dynamics}, "
            f"Amount={self.amount}, "
            f"Mass={self.mass}"
        )

    def speeds(self, mech_total_mass):
        speed = 0
        friction = self.anchor * mech_total_mass / 100
        print("Friction", friction)
        accel = self.thrust * self.amount / mech_total_mass
        accel -= friction
        print("Acceleration", accel)
        speeds = []
        for i in range(1000):
            speed += accel
            if self.dynamics == 0:
                air = speed * speed * speed
            else:
                air = speed * speed / (10 * self.dynamics)
            speed -= air
            if speed <= 0:
                speed = 0
            speeds.append(speed)
        return speeds

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            "Thrust": self.thrust,
            "Anchor": self.anchor,
            "Dynamics": self.dynamics,
            "Enabled": self.enabled,
        }

    def use(self, parameter):
        if not parameter:  # default is toggle
            self.enabled = "[ ]" if self.is_active() else "[x]"
        elif parameter in ("disable", "enable"):
            self.enabled = "[ ]" if "-" in self.enabled else "-"
