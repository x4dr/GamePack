"""Movement system for EndWorld.

Handles thrust, drag, and speed calculations for ship movement.
"""

from typing import Any, ClassVar

from gamepack.endworld.System import System


class MovementSystem(System):
    """A system that provides thrust, anchoring, and dynamic movement.

    Simulates acceleration with quadratic drag and friction over time.
    """

    headers: ClassVar[list[str]] = [
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

    def __init__(self, name: str, data: dict[str, Any]):
        """Initialise a MovementSystem from parsed configuration data.

        Args:
            name: Human-readable system name.
            data: Raw configuration dictionary with ``thrust``, ``anchor``,
                and ``dynamics`` keys.

        """
        super().__init__(name, data)
        self.thrust = self.number(self.extract("thrust"))
        self.anchor = self.number(self.extract("anchor"))
        self.dynamics = self.number(self.extract("dynamics"))

    def __repr__(self) -> str:
        """Return a string representation of the movement system."""
        return (
            f"Movement System {self.name}: "
            f"Thrust={self.thrust}, "
            f"Anchor={self.anchor}, "
            f"Dynamics={self.dynamics}, "
            f"Amount={self.amount}, "
            f"Mass={self.mass}"
        )

    def speeds(self, mech_total_mass: float, initial_speed: float = 0.0) -> list[float]:
        """Simulate acceleration over time and return speeds at each second.

        Models thrust force against friction, quadratic drag, and mass
        to produce a list of speeds in km/h.

        Args:
            mech_total_mass: Total mass of the mech in tons.
            initial_speed: Starting speed in km/h (default ``0.0``).

        Returns:
            list[float]: Speed in km/h at each simulated second.

        """
        dt = 0.1  # timestep in seconds
        speed = initial_speed / 3.6  # convert kmh to m/s
        speeds_list = [speed * 3.6]

        thrust_force = self.thrust * self.amount  # kN
        # Friction scales with mass (Anchor is kN per ton)
        friction_force = self.anchor * mech_total_mass  # kN

        accel = 1.0
        step = 1

        while accel > 0.0001 and step < 2000:  # Cap at 200s
            # Quadratic drag: F_drag = v^2 / (Dyn / 10)
            # Scaling by 10 allows 'natural' 1-100 dynamics values
            drag_force = (speed**2) / ((self.dynamics / 10.0) if self.dynamics > 0 else 0.01)

            if mech_total_mass <= 0:
                break

            # a = F/m (kN / tons = m/s^2)
            net_force = thrust_force - friction_force - drag_force
            accel = net_force / mech_total_mass

            if accel < 0 and speed <= 0:
                accel = 0
                speed = 0

            speed += accel * dt
            speed = max(speed, 0)

            if step % int(1 / dt) == 0:
                speeds_list.append(speed * 3.6)  # kmh
            step += 1

        return speeds_list

    def to_dict(self) -> dict[str, str]:
        """Serialise the movement system to a dictionary for table rendering."""
        return {
            **super().to_dict(),
            "Thrust": f"{self.thrust:g}",
            "Anchor": f"{self.anchor:g}",
            "Dynamics": f"{self.dynamics:g}",
            "Enabled": self.enabled,
        }
