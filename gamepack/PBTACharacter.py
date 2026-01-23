from typing import List, Dict, Tuple, Optional, Self, Union, Callable
from gamepack.Item import tryfloatdefault
from gamepack.MDPack import MDObj, MDTable, MDChecklist
from gamepack.PBTAItem import PBTAItem


class PBTACharacter:
    def __init__(
        self,
        info: Dict[str, str],
        moves: List[Tuple[str, bool]],
        health: Dict[str, Union[Dict, List]],
        stats: Dict[str, Dict],
        inventory: Optional[List[PBTAItem]] = None,
        inventory_bonus_headers: Optional[set[str]] = None,
        notes: str = "",
        meta: Optional[Dict[str, MDObj]] = None,
        errors: Optional[List[str]] = None,
    ):
        self.info = info
        self.moves = moves
        self.health = health
        self.stats = stats
        self.inventory = inventory or []
        self.inventory_bonus_headers = inventory_bonus_headers or set()
        self.notes = notes
        self.meta = meta or {}
        self.errors = errors or []

    info_headings = ["info"]
    health_headings = ["health", "damage"]
    current_headings = ["current", "cur"]
    max_headings = ["maximum", "max"]
    type_headings = ["type", "name", "stat"]
    moves_headings = ["moves"]
    stats_headings = ["stats", "attributes"]
    inventory_headings = ["inventory", "gear"]
    note_headings = ["notes"]
    stat_structure = {
        "Insight": ["Hunt", "Study", "Survey", "Tinker"],
        "Prowess": ["Skirmish", "Finesse", "Prowl", "Wreck"],
        "Resolve": ["Attune", "Command", "Consort", "Sway"],
    }
    stat_table_headers = ["Stat", "Value"]
    wound_headings = ["harm", "wounds", "wunden", "injuries", "verletzungen"]

    def post_process(self, flash: Callable[[str], None]):
        # tally inventory
        for k in list(self.meta.keys()):
            if k.lower() in self.inventory_headings:
                self.process_inventory(self.meta[k], flash)
                del self.meta[k]
            elif k.lower() in self.note_headings:
                self.notes = self.meta[k].plaintext
                del self.meta[k]

    def process_inventory(self, node: MDObj, flash: Callable[[str], None]):
        for table in node.tables:
            items, headers = PBTAItem.process_table(table)
            self.inventory.extend(items)
            self.inventory_bonus_headers.update(headers)
        for content in node.children.values():
            self.process_inventory(content, flash)

    @classmethod
    def from_mdobj(
        cls, body: MDObj, handle_error: Optional[Callable[[str], None]] = None
    ) -> Self:
        errors = []
        if not handle_error:
            handle_error = errors.append

        info = {}
        health = {}
        moves = []
        stats = {}
        meta = {}

        for k, v in body.children.items():
            k_lower = k.lower().strip()
            if k_lower in cls.info_headings:  # processing basic info
                info, err = v.confine_to_tables()
                for e in err:
                    handle_error(e)
            elif k_lower in cls.moves_headings:
                moves = v.all_checklists
            elif k_lower in cls.stats_headings:
                stats, err = v.confine_to_tables()
                for e in err:
                    handle_error(e)
            elif k_lower in cls.health_headings:
                health = {}
                for t in v.tables:
                    name_idx = t.header_pos(cls.type_headings, 0)
                    cur_idx = t.header_pos(cls.current_headings, 1)
                    max_idx = t.header_pos(cls.max_headings, 2)
                    for row in t.rows:
                        if len(row) > max(name_idx, cur_idx, max_idx):
                            health[row[name_idx].title()] = {
                                cls.current_headings[0].title(): row[cur_idx],
                                cls.max_headings[0].title(): row[max_idx],
                            }
                for section, child in v.children.items():
                    if section.lower().strip() in cls.wound_headings:
                        for severity, description_obj in child.children.items():
                            text = description_obj.plaintext.strip()
                            health[severity] = [w for w in text.splitlines(False) if w]
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

    def health_get(self, key: str) -> tuple[int, int]:
        h = self.health.get(key.title())
        if not h or not isinstance(h, dict):
            return 1, 1

        cur_key = self.current_headings[0].title()
        max_key = self.max_headings[0].title()

        try:
            current = int(tryfloatdefault(h.get(cur_key), 1.0))
        except (ValueError, TypeError):
            current = 1
        try:
            maximum = int(tryfloatdefault(h.get(max_key), 1.0))
        except (ValueError, TypeError):
            maximum = 1
        return current, maximum

    @classmethod
    def from_md(cls, body: str, flash: Optional[Callable[[str], None]] = None) -> Self:
        sheet_parts = MDObj.from_md(body)
        return cls.from_mdobj(sheet_parts, flash)

    def to_md(self) -> str:
        return self.to_mdobj().to_md()

    def to_mdobj(self, error_handler: Optional[Callable[[str], None]] = None) -> MDObj:
        if not error_handler:

            def default_error_handler(error):
                self.errors.append(error)

            error_handler = default_error_handler

        sections = MDObj("", flash=error_handler)

        # Basic Information Section
        info_mdo = MDObj("", flash=error_handler, header=self.info_headings[0].title())
        for key, value in self.info.items():
            info_mdo.add_child(MDObj(str(value), flash=error_handler, header=key))
        sections.add_child(info_mdo)

        # Health Section
        health_mdo = MDObj(
            "", flash=error_handler, header=self.health_headings[0].title()
        )
        harm_mdo = MDObj("", header=self.wound_headings[0])

        health_rows = []
        for key, val in self.health.items():
            if isinstance(val, list):
                harm_mdo.add_child(
                    MDObj("\n".join(val), flash=error_handler, header=key)
                )
            elif isinstance(val, dict):
                health_rows.append(
                    [
                        key,
                        str(val.get(self.current_headings[0].title(), "")),
                        str(val.get(self.max_headings[0].title(), "")),
                    ]
                )

        if harm_mdo.children:
            health_mdo.add_child(harm_mdo)

        if health_rows:
            health_mdo.tables.append(
                MDTable(health_rows, ["Type", "Current", "Maximum"])
            )

        sections.add_child(health_mdo)

        # Moves Section
        if self.moves:
            sections.add_child(
                MDObj(
                    "",
                    lists=[MDChecklist(self.moves)],
                    header=self.moves_headings[0].title(),
                )
            )

        # Stats Section
        sections.add_child(self._create_stats_section())

        # Inventory Section
        inventory_section = self._create_inventory_section(error_handler)
        if inventory_section:
            sections.add_child(inventory_section)

        if self.notes:
            sections.add_child(MDObj(self.notes, header="Notes"))

        return sections

    def _create_stats_section(self) -> MDObj:
        result = MDObj("", header=self.stats_headings[0].title())
        for category, skills in self.stat_structure.items():
            data = [
                [skill, str(self.stats.get(category, {}).get(skill, "0"))]
                for skill in skills
            ]
            result.add_child(
                MDObj(
                    "",
                    header=category.title(),
                    tables=[MDTable(data, self.stat_table_headers)],
                )
            )
        return result

    def _create_inventory_section(
        self, error_handler: Callable[[str], None]
    ) -> Optional[MDObj]:
        if not self.inventory:
            return None

        headers = ["Name", "Quantity", "Maximum", "Description"]
        bonus_headers = sorted(list(self.inventory_bonus_headers))
        headers.extend(bonus_headers)

        rows = []
        for item in self.inventory:
            row = [
                item.name,
                f"{item.count:g}",
                str(item.maximum),
                item.description,
            ]
            for h in bonus_headers:
                row.append(item.additional_info.get(h, ""))
            rows.append(row)

        rows.append(["Total"] + (len(headers) - 1) * [""])
        # total_table from gamepack.Item could be used here if compatible

        inventory_table = MDTable(rows, headers)
        return MDObj(
            "", flash=error_handler, tables=[inventory_table], header="Inventory"
        )

    def inventory_get(self, name: str) -> Optional[PBTAItem]:
        for i in self.inventory:
            if i.name == name:
                return i
        return None
