from .MDPack import MDObj, MDTable
from .PBTAItem import PBTAItem


class PBTACharacter:
    def __init__(
        self,
        info,
        moves,
        health,
        stats,
        inventory=None,
        inventory_bonus_headers=None,
        notes=None,
        meta=None,
        errors=None,
    ):
        self.info: dict[str, str] = info
        self.moves: list[str] = moves
        self.health: dict[str, (int, int)] = health
        self.stats: dict[str, dict] = stats
        self.inventory = inventory or []
        self.inventory_bonus_headers = (
            set() if inventory_bonus_headers is None else inventory_bonus_headers
        )
        self.notes = notes or ""
        self.meta = {} if meta is None else meta
        self.errors = [] if errors is None else errors

    info_headings = ["info"]
    health_headings = ["health", "damage"]
    current_headings = ["current", "cur"]
    max_headings = ["maximum", "max"]
    type_headings = ["type", "name", "stat"]
    moves_headings = ["moves"]
    stats_headings = ["stats", "attributes"]
    inventory_headings = ["inventory", "gear"]
    note_headings = ["notes"]

    def post_process(self, flash):
        # tally inventory
        for k in self.meta.keys():
            if k.lower() in self.inventory_headings:
                self.process_inventory(self.meta[k], flash)
            if k.lower() in self.note_headings:
                self.notes = self.meta[k].plaintext

    def process_inventory(self, node: MDObj, flash):

        for table in node.tables:
            items, headers = PBTAItem.process_table(table)
            self.inventory.extend(items)
            self.inventory_bonus_headers.update(headers)
        for content in node.children.values():
            self.process_inventory(content, flash)

    @classmethod
    def from_mdobj(cls, body: MDObj, handle_error=None):
        errors = []
        if not handle_error:
            handle_error = errors.append

        info = {}
        health = {}
        moves = []
        stats = {}
        meta = {}

        for k, v in body.children.items():
            if k.lower() in cls.info_headings:  # processing basic info
                info, err = v.confine_to_tables()
                handle_error(err)
            elif k.lower() in cls.moves_headings:
                for move in v.tables[0].rows:
                    moves.append(move[0])
            elif k.lower() in cls.stats_headings:
                stats, err = v.confine_to_tables()
                handle_error(err)
            elif k.lower() in cls.health_headings:
                health = {}
                for t in v.tables:
                    name = t.header_pos(cls.type_headings, 0)
                    current = t.header_pos(cls.current_headings, 1)
                    maximum = t.header_pos(cls.max_headings, 2)
                    health.update(
                        {
                            row[name].title(): {
                                cls.current_headings[0].title(): row[current],
                                cls.max_headings[0].title(): row[maximum],
                            }
                            for row in t.rows
                        }
                    )
            else:
                meta[k] = v

        character = cls(
            info=info,
            moves=moves,
            health=health,
            stats=stats,
            meta=meta,
            errors=errors,
        )
        character.post_process(handle_error)
        return character

    def health_get(self, key: str) -> (int, int):
        h = self.health[key.title()]

        try:
            current = int(h[self.current_headings[0].title()])
        except ValueError:
            current = 1
        try:
            maximum = int(h[self.max_headings[0].title()])
        except ValueError:
            maximum = 1
        return current, maximum

    @classmethod
    def from_md(cls, body: str, flash=None):
        sheetparts = MDObj.from_md(body)
        return cls.from_mdobj(sheetparts, flash)

    def to_md(self):
        return self.to_mdobj().to_md()

    def to_mdobj(self, error_handler=None):
        if not error_handler:

            def default_error_handler(error):
                self.errors.append(error)

            error_handler = default_error_handler

        sections = MDObj("", flash=error_handler)

        # Basic Information Section
        info = MDObj("", {}, error_handler, header=self.info_headings[0].title())
        for key, value in self.info.items():
            info.add_child(MDObj(value, {}, error_handler, header=key))
        sections.add_child(info)

        # Health Section
        health = MDObj(
            "",
            {},
            error_handler,
            header=self.health_headings[0].title(),
        )

        rows = [
            [stat, str(current), str(maximum)]
            for stat, (current, maximum) in self.health.items()
        ]
        headers = ["Type", "Current", "Maximum"]
        health_table = MDTable(rows, headers)
        health.tables.append(health_table)
        sections.add_child(health)

        # Moves Section
        moves_table = self._create_moves_table()
        sections.add_child(
            MDObj(
                "",
                {},
                error_handler,
                [moves_table],
                header=self.moves_headings[0].title(),
            )
        )

        # Stats Section
        stats_table = self._create_stats_table()
        sections.add_child(
            MDObj(
                "",
                {},
                error_handler,
                [stats_table],
                header=self.stats_headings[0].title(),
            )
        )

        # Inventory Section
        inventory_section = self._create_inventory_section(error_handler)
        sections.add_child(inventory_section)
        sections.add_child(MDObj(self.notes, header="Notes"))

        return sections

    def _create_moves_table(self):
        if not self.moves:
            return None
        headers = ["Move"]
        rows = [[move] for move in self.moves]
        return MDTable(rows, headers)

    def _create_stats_table(self):
        if not self.stats:
            return None
        headers = ["Stat", "Value"]
        data = []
        for k, v in self.stats.items():
            data.append([k, v])
        return MDTable(data, headers)

    def _create_inventory_section(self, error_handler):
        if not self.inventory:
            return None

        headers = [
            "Name",
            "Quantity",
            "Load",
            "Description",
        ]
        headers.extend(self.inventory_bonus_headers)
        rows = [
            [
                f"{item.name}",
                f"{item.count:g}",
                item.load,
                item.description,
            ]
            + [item.additional_info.get(x) or "" for x in self.inventory_bonus_headers]
            for item in self.inventory
        ]
        total_row = ["Total"] + (len(headers) - 1) * [""]
        rows.append(total_row)
        inventory_table = MDTable(rows, headers)
        return MDObj("", {}, error_handler, [inventory_table], header="Inventory")
