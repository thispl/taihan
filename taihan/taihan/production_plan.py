import frappe
from frappe import _
from frappe.utils import cint, flt
from erpnext.manufacturing.doctype.production_plan.production_plan import ProductionPlan


class CustomProductionPlan(ProductionPlan):
    def validate(self):
        super().validate()
        validate_production_plan_doc(self)

    @frappe.whitelist()
    def get_sub_assembly_items(self, manufacturing_type=None):
        super().get_sub_assembly_items(manufacturing_type)
        self.process_sub_assembly_items()

    def process_sub_assembly_items(self):
        warehouse_map = {
            "Buffering": "Buffering - TKFOC",
            "Stranding": "Stranding - TKFOC",
            "Jacketing": "Jacketing - TKFOC",
        }

        bom_ops_cache = {}

        def get_bom_operation(bom_no):
            if not bom_no:
                return None
            if bom_no not in bom_ops_cache:
                bom_ops = frappe.get_all(
                    "BOM Operation",
                    filters={"parent": bom_no},
                    fields=["operation"],
                    order_by="idx asc",
                    limit=1,
                )
                bom_ops_cache[bom_no] = bom_ops[0].operation if bom_ops else None
            return bom_ops_cache[bom_no]

        # Step 1: Map warehouse based on BOM operations if available
        for row in self.sub_assembly_items:
            if row.get("bom_no"):
                op = get_bom_operation(row.get("bom_no"))
                warehouse = warehouse_map.get(op)
                if warehouse:
                    row.fg_warehouse = warehouse

        # Step 2: Get selected tube colors from Production Plan
        tube_colors = [
            str(d.get("tube_color") if hasattr(d, "get") else getattr(d, "tube_color", "")).strip()
            for d in self.get("custom_tube_color", [])
            if (d.get("tube_color") if hasattr(d, "get") else getattr(d, "tube_color", None))
        ]
        selected_color_map = {c.lower(): c for c in tube_colors}
        tube_color_indices = {c.lower(): idx for idx, c in enumerate(tube_colors)}

        # Step 3: Find Stranding quantity and BOM mapping
        stranding_qty_map = {}
        stranding_bom_map = {}
        for row in self.sub_assembly_items:
            fg_wh = str(row.get("fg_warehouse") or "").strip().lower()
            if "stranding" in fg_wh:
                pp_item = (
                    row.get("production_plan_item")
                    if hasattr(row, "get")
                    else getattr(row, "production_plan_item", None)
                )
                parent_item = (
                    row.get("parent_item_code")
                    if hasattr(row, "get")
                    else getattr(row, "parent_item_code", None)
                )
                prod_item = (
                    row.get("production_item")
                    if hasattr(row, "get")
                    else getattr(row, "production_item", None)
                )
                qty = flt(row.get("qty") if hasattr(row, "get") else getattr(row, "qty", 0))
                bom_no = (
                    row.get("bom_no")
                    if hasattr(row, "get")
                    else getattr(row, "bom_no", None)
                )
                if pp_item and prod_item:
                    stranding_qty_map[(pp_item, prod_item)] = qty
                    stranding_bom_map[(pp_item, prod_item)] = bom_no
                if pp_item:
                    stranding_qty_map[pp_item] = qty
                    stranding_bom_map[pp_item] = bom_no
                if prod_item:
                    stranding_qty_map[prod_item] = qty
                    stranding_bom_map[prod_item] = bom_no
                if parent_item:
                    stranding_qty_map[parent_item] = qty
                stranding_qty_map["_default"] = qty

        stranding_buffering_cache = {}

        def get_stranding_buffering_info(bom_no):
            if not bom_no:
                return {}, False
            if bom_no not in stranding_buffering_cache:
                bom_items = frappe.get_all(
                    "BOM Item",
                    filters={"parent": bom_no},
                    fields=["item_code", "bom_no", "custom_tube_colour"],
                )
                item_color_map = {}
                has_tube_colors = False
                for bi in bom_items:
                    if bi.bom_no:
                        op = get_bom_operation(bi.bom_no)
                        if op and op.lower() == "buffering":
                            color = bi.custom_tube_colour or frappe.db.get_value(
                                "Item", bi.item_code, "custom_tube_colour"
                            )
                            if color:
                                color_clean = str(color).strip()
                                item_color_map[bi.item_code] = color_clean
                                has_tube_colors = True
                            else:
                                item_color_map[bi.item_code] = None
                stranding_buffering_cache[bom_no] = (item_color_map, has_tube_colors)
            return stranding_buffering_cache[bom_no]

        # Step 4: Process sub assembly items
        new_sub_assembly_items = []
        buffering_rows_to_sort = []

        for row in self.sub_assembly_items:
            fg_wh = (
                row.get("fg_warehouse")
                if hasattr(row, "get")
                else getattr(row, "fg_warehouse", "")
            ) or ""
            fg_wh = str(fg_wh).strip().lower()
            is_buffering = "buffering" in fg_wh

            if not is_buffering or not tube_colors:
                row_dict = (
                    row.as_dict()
                    if hasattr(row, "as_dict")
                    else dict(row)
                )
                row_dict.pop("name", None)
                new_sub_assembly_items.append(row_dict)
            else:
                pp_item = (
                    row.get("production_plan_item")
                    if hasattr(row, "get")
                    else getattr(row, "production_plan_item", None)
                )
                parent_item = (
                    row.get("parent_item_code")
                    if hasattr(row, "get")
                    else getattr(row, "parent_item_code", None)
                )

                parent_bom = (
                    stranding_bom_map.get((pp_item, parent_item))
                    or stranding_bom_map.get(parent_item)
                    or stranding_bom_map.get(pp_item)
                )
                if not parent_bom and parent_item:
                    parent_bom = frappe.db.get_value(
                        "BOM", {"item": parent_item, "is_active": 1, "is_default": 1}
                    )

                item_color_map, has_tube_colors = get_stranding_buffering_info(parent_bom)

                stranding_qty = (
                    stranding_qty_map.get((pp_item, parent_item))
                    or stranding_qty_map.get(parent_item)
                    or stranding_qty_map.get(pp_item)
                    or stranding_qty_map.get("_default")
                )

                orig_qty = flt(row.get("qty") if hasattr(row, "get") else getattr(row, "qty", 0))
                num_colors = len(tube_colors)

                if stranding_qty:
                    target_qty = stranding_qty
                elif num_colors > 0:
                    target_qty = orig_qty / num_colors
                else:
                    target_qty = orig_qty

                if has_tube_colors:
                    # Filter tube colors defined in BOM
                    item_code = (
                        row.get("production_item")
                        if hasattr(row, "get")
                        else getattr(row, "production_item", None)
                    )
                    raw_color = (
                        item_color_map.get(item_code)
                        or (row.get("custom_tube_colour") if hasattr(row, "get") else getattr(row, "custom_tube_colour", None))
                        or frappe.db.get_value("Item", item_code, "custom_tube_colour")
                    )
                    row_color = str(raw_color).strip() if raw_color else ""
                    norm_color = row_color.lower()

                    if norm_color in selected_color_map:
                        canonical_color = selected_color_map[norm_color]
                        row_dict = (
                            row.as_dict()
                            if hasattr(row, "as_dict")
                            else dict(row)
                        )
                        row_dict.pop("name", None)
                        row_dict["custom_tube_colour"] = canonical_color
                        row_dict["qty"] = target_qty
                        sort_key = tube_color_indices.get(norm_color, 999)
                        buffering_rows_to_sort.append((sort_key, row_dict))
                    # Exclude unselected colors and generic uncolored buffering rows
                else:
                    # Existing flow: duplicate for each selected tube color
                    for color in tube_colors:
                        row_dict = (
                            row.as_dict()
                            if hasattr(row, "as_dict")
                            else dict(row)
                        )
                        row_dict.pop("name", None)
                        row_dict["custom_tube_colour"] = color
                        row_dict["qty"] = target_qty
                        new_sub_assembly_items.append(row_dict)

        # Append sorted buffering rows from BOM-defined colors
        if buffering_rows_to_sort:
            buffering_rows_to_sort.sort(key=lambda x: x[0])
            for _, row_dict in buffering_rows_to_sort:
                new_sub_assembly_items.append(row_dict)

        # Step 5: Re-assign idx and set back to sub_assembly_items
        self.set("sub_assembly_items", [])
        for idx, row_dict in enumerate(new_sub_assembly_items):
            row_dict["idx"] = idx + 1
            self.append("sub_assembly_items", row_dict)


def validate_production_plan_doc(doc):
    fiber_count = cint(doc.get("custom_fiber_count"))

    if fiber_count:
        # Validate Fiber Count is a multiple of 12
        if fiber_count % 12 != 0 or fiber_count <= 0:
            frappe.throw(_("Fiber Count should be multiple of 12."))

        expected_no_of_colours = fiber_count // 12
        doc.custom_no_of_colours = expected_no_of_colours

        # Validate duplicate Tube Colours if any
        tube_colors = [
            (d.get("tube_color") if hasattr(d, "get") else getattr(d, "tube_color", None))
            for d in doc.get("custom_tube_color", [])
            if (d.get("tube_color") if hasattr(d, "get") else getattr(d, "tube_color", None))
        ]
        unique_tube_colors = set(tube_colors)

        if len(unique_tube_colors) != len(tube_colors):
            frappe.throw(_("Duplicate tube colours are not allowed."))

        if len(tube_colors) != expected_no_of_colours:
            frappe.throw(
                _("Number of selected Tube Colours should be equal to No. of Colours.")
            )

    # Validate Buffering rows have Tube Colour assigned
    if doc.get("sub_assembly_items"):
        for row in doc.get("sub_assembly_items"):
            fg_wh = (
                row.get("fg_warehouse")
                if hasattr(row, "get")
                else getattr(row, "fg_warehouse", "")
            ) or ""
            fg_wh = str(fg_wh).strip().lower()
            if "buffering" in fg_wh:
                tube_col = (
                    row.get("custom_tube_colour")
                    if hasattr(row, "get")
                    else getattr(row, "custom_tube_colour", None)
                )
                if not tube_col:
                    idx = (
                        row.get("idx")
                        if hasattr(row, "get")
                        else getattr(row, "idx", "")
                    )
                    prod_item = (
                        row.get("production_item")
                        if hasattr(row, "get")
                        else getattr(row, "production_item", "")
                    )
                    frappe.throw(
                        _(
                            "Row #{0}: Tube Colour is required for Buffering Sub Assembly item {1}."
                        ).format(idx, prod_item)
                    )


@frappe.whitelist()
def validate_production_plan(doc, method=None):
    validate_production_plan_doc(doc)


@frappe.whitelist()
def get_operation_warehouse(bom):
    bom_doc = frappe.get_doc("BOM", bom)

    if not bom_doc.operations:
        return ""

    operation = bom_doc.operations[0].operation

    mapping = {
        "Buffering": "Buffering - TKFOC",
        "Stranding": "Stranding - TKFOC",
        "Jacketing": "Jacketing - TKFOC",
    }

    return mapping.get(operation)


@frappe.whitelist()
def update_warehouse_sub_assembly_item(doc, method=None):
    warehouse_map = {
        "Buffering": "Buffering - TKFOC",
        "Stranding": "Stranding - TKFOC",
        "Jacketing": "Jacketing - TKFOC",
    }

    # Sub Assembly Items
    for row in doc.get("sub_assembly_items", []):
        if row.get("bom_no"):
            bom = frappe.get_doc("BOM", row.get("bom_no"))

            if bom.operations:
                operation = bom.operations[0].operation
                warehouse = warehouse_map.get(operation)

                if warehouse:
                    row.fg_warehouse = warehouse