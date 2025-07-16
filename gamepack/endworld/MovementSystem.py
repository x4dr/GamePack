from gamepack.endworld.System import System


@System.register("Movement")
class MovementSystem(System):
    headers = ["Energy", "Heat", "Thrust", "Anchor", "Dynamics", "Mass", "Amount"]

    def __init__(self, name, data):
        super().__init__(name, data)
        self.thrust = self.number(self.extract("thrust"))
        self.anchor = self.number(self.extract("anchor"))
        self.dynamics = self.number(self.extract("dynamics"))

    def speeds(self, mech_total_mass):
        speed = 0
        friction = self.anchor * mech_total_mass / 100
        accel = self.thrust / mech_total_mass
        speeds = []
        for i in range(10000):
            speed += accel
            speed -= friction
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
        }
