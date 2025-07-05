__author__ = "maric"

from gamepack.MDPack import MDObj, MDTable


class Mecha:
    def __init__(self):
        self.description = {}
        self.errors = []
        self.systems: dict[str, dict] = {}

    @classmethod
    def from_mdobj(cls, mdobj):
        self = cls()

        def flash(err):
            self.errors.append(err)

        # inform about things that should not be there
        if mdobj.plaintext.strip():
            flash("Loose Text: " + mdobj.plaintext)

        for t in mdobj.tables:
            if t:
                flash("Loose Table:" + t.to_md())

        self.systems["Movement"] = []
        self.systems["Energy"] = []
        self.systems["Heat"] = []
        self.systems["Offensive"] = []
        self.systems["Defensive"] = []
        self.systems["Support"] = []
        self.systems["Seal"] = []

        for key in self.systems.keys():
            sys: MDObj = mdobj.children.get("Systems", MDObj.empty()).children.get(
                key, MDObj.empty()
            )
            tables = sys.confine_to_tables(True)
            print("tables:", tables, "tables.")
            self.systems[key] = tables[0]
        self.post_process(flash)
        return self

    def speeds(self):
        totalmass = 0
        for system_category, systems in self.systems.items():
            totalmass += sum(
                [float(x["Mass"]) * float(x["Amount"]) for x in systems.values()]
            )

        for mname, msys in self.systems["Movement"].items():
            speed = 0
            friction = float(msys["Static"]) * totalmass / 100
            accel = float(msys["Thrust"]) / totalmass
            print(mname, accel, friction)
            speeds = []
            for i in range(10000):
                speed += accel
                speed -= friction
                air = float(msys["Friction"]) * speed * speed / 100
                speed -= air
                if speed <= 0:
                    speed = 0
                speeds.append(speed)
            final = speeds[-1]
            threshold = final * 0.9
            for idx, val in enumerate(speeds):
                if val >= threshold:
                    print(
                        f"speed 1 5 and 15 {(speeds[1],speeds[5], speeds[15])}max speed reached after {idx}seconds, at {val}"
                    )
                    break
        return totalmass

    def post_process(self, flash):
        pass

    def to_mdobj(self):

        def flash(err):
            self.errors.append(err)

        description = MDObj(
            "",
            flash=flash,
            header="Description",
        )
        for k, v in self.description.items():
            description.add_child(MDObj(v, flash=flash, header=k))

        systems = self.construct_mdobj_from_systems(
            self.systems, list(self.systems.keys()), flash
        ).with_header("Systems")

        mdo = MDObj("")
        mdo.add_child(description)
        mdo.add_child(systems)
        return mdo

    @classmethod
    def construct_mdobj_from_systems(
        cls, systems_dict: dict, headings: list[str], flash
    ) -> MDObj:
        if not systems_dict:
            return MDObj("", {}, flash)
        systems = MDObj.empty()
        for system_cat, sys in systems_dict.items():
            rows = []
            headers = []
            for sys_name, sys_stats in sys.items():
                row = [sys_name]
                headers = list(sys_stats.keys())
                for h in headers:
                    row.append(sys_stats[h])
                rows.append(row)
            headers = [""] + headers
            table = MDTable(rows, headers)
            systems.add_child(MDObj("", tables=[table], header=system_cat))
        return systems
