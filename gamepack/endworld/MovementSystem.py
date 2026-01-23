from typing import List, Dict, Any
from gamepack.endworld.System import System


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

    thrust: float
    anchor: float
    dynamics: float

    def __init__(self, name: str, data: Dict[str, Any]):
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

    def speeds(self, mech_total_mass: float) -> List[float]:
        dt = 0.1  # timestep in seconds

        speed = 0.0  # m/s
        speeds_list = [speed]

        thrust_force = self.thrust * self.amount  # N
        friction_force = self.anchor * mech_total_mass  # N
        accel = 1.0
        step = 1
        # print("\n", self.name, mech_total_mass, "t")
        while accel > 0.001:
            if self.dynamics == 0:
                drag_force = speed**3
            else:
                drag_force = speed**2 / (self.dynamics / 10)

            if mech_total_mass <= 0:
                break

            accel = (thrust_force - friction_force - drag_force) / (
                mech_total_mass * 10
            )
            speed += accel * dt
            if speed < 0:
                speed = 0.0

            if step % int(1 / dt) == 0:
                # print(thrust_force, friction_force, drag_force, end="=")
                speeds_list.append(speed * 3.6)  # kmh
                # print(f"{accel=},    {step} {speed}")
            step += 1

        return speeds_list

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            "Thrust": self.thrust,
            "Anchor": self.anchor,
            "Dynamics": self.dynamics,
            "Enabled": self.enabled,
        }
