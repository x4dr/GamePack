from Item import Item
from MDPack import MDObj, MDTable


class PBTACharacter:
    def __init__(
        self,
        info=None,
        moves=None,
        stats=None,
        inventory=None,
        inventory_bonus_headers=None,
        notes=None,
        meta=None,
        errors=None,
    ):
        self.info = {} if info is None else info
        self.moves = [] if moves is None else moves
        self.stats = {} if stats is None else stats
        self.inventory = [] if inventory is None else inventory
        self.inventory_bonus_headers = (
            set() if inventory_bonus_headers is None else inventory_bonus_headers
        )
        self.notes = notes or ""
        self.meta = {} if meta is None else meta
        self.errors = [] if errors is None else errors

    info_headings = {"info"}
    moves_headings = {"moves"}
    stats_headings = {"stats", "attributes"}
    inventory_headings = {"inventory", "gear"}
    note_headings = {"notes"}

    def post_process(self, flash):
        # tally inventory
        for k in self.meta.keys():
            if k.lower() in self.inventory_headings:
                self.process_inventory(self.meta[k], flash)
            if k.lower() in self.note_headings:
                self.notes = self.meta[k].plaintext

    def process_inventory(self, node: MDObj, flash):
        for table in node.tables:
            items, headers = Item.process_table(table, flash)
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
            else:
                meta[k] = v

        character = cls(
            info=info,
            moves=moves,
            stats=stats,
            meta=meta,
            errors=errors,
        )
        character.post_process(handle_error)
        return character

    @classmethod
    def from_md(cls, body: str, flash=None):
        sheetparts = MDObj.from_md(body)
        return cls.from_mdobj(sheetparts, flash)

    def to_mdobj(self, error_handler=None):
        if not error_handler:

            def default_error_handler(error):
                self.errors.append(error)

            error_handler = default_error_handler

        sections = MDObj("", flash=error_handler)

        # Basic Information Section
        info = MDObj("", {}, error_handler, header="Info")
        for key, value in self.info.items():
            info.add_child(MDObj(value, {}, error_handler, header=key))
        sections.add_child(info)

        # Moves Section
        moves_table = self._create_moves_table()
        sections.add_child(MDObj("", {}, error_handler, [moves_table], header="Moves"))

        # Stats Section
        stats_table = self._create_stats_table()
        sections.add_child(MDObj("", {}, error_handler, [stats_table], header="Stats"))

        # Inventory Section
        inventory_section = self._create_inventory_section(error_handler)
        sections.add_child(inventory_section)
        # Notes Section
        sections.add_child(MDObj(self.notes))

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
            "Weight",
            "Price",
            "Total Weight",
            "Total Price",
            "Description",
        ]
        headers.extend(self.inventory_bonus_headers)
        rows = [
            [
                f"{item.name}",
                f"{item.count:g}",
                item.singular_weight,
                item.singular_price,
                item.total_weight,
                item.total_price,
                item.description,
            ]
            + [item.additional_info.get(x) or "" for x in self.inventory_bonus_headers]
            for item in self.inventory
        ]
        total_row = ["Total"] + (len(headers) - 1) * [""]
        rows.append(total_row)
        inventory_table = MDTable(rows, headers)
        return MDObj("", {}, error_handler, [inventory_table], header="Inventory")
