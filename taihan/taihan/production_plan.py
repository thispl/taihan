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
        if self.skip_available_sub_assembly_item and not self.sub_assembly_warehouse:
            frappe.throw(_("Please select the Sub Assembly Warehouse"))

        skip_flag = self.skip_available_sub_assembly_item
        self.skip_available_sub_assembly_item = 0
        try:
            super().get_sub_assembly_items(manufacturing_type)
        finally:
            self.skip_available_sub_assembly_item = skip_flag

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

        # Stock deduction setup
        is_all_warehouses = False
        selected_wh = ""
        stock_cache = {}

        def get_stock_data(item_code, wh_name):
            cache_key = (item_code, wh_name)
            if cache_key not in stock_cache:
                bin_data = frappe.db.get_value(
                    "Bin",
                    {"item_code": item_code, "warehouse": wh_name},
                    ["actual_qty", "reserved_qty_for_production"],
                    as_dict=True,
                )
                act_qty = flt(bin_data.actual_qty) if bin_data else 0.0
                res_qty = flt(bin_data.reserved_qty_for_production) if bin_data else 0.0
                avail_qty = max(0.0, act_qty - res_qty)
                stock_cache[cache_key] = {
                    "actual_qty": act_qty,
                    "available_qty": avail_qty,
                }
            return stock_cache[cache_key]

        if self.skip_available_sub_assembly_item and self.sub_assembly_warehouse:
            selected_wh = (self.sub_assembly_warehouse or "").strip()
            if selected_wh:
                wh_doc = frappe.db.get_value(
                    "Warehouse", selected_wh, ["name", "is_group"], as_dict=True
                )
                if wh_doc and (wh_doc.is_group or "all warehouse" in str(wh_doc.name).lower()):
                    is_all_warehouses = True
                elif "all warehouse" in selected_wh.lower():
                    is_all_warehouses = True

        def apply_stock_deduction(prod_item, row_wh, current_qty):
            should_reduce = False
            if is_all_warehouses:
                should_reduce = True
            elif row_wh and row_wh.lower() == selected_wh.lower():
                should_reduce = True

            actual_stock = 0.0
            if prod_item and row_wh:
                stock_info = get_stock_data(prod_item, row_wh)
                actual_stock = stock_info["actual_qty"]
                if should_reduce:
                    avail_stock = stock_info["available_qty"]
                    if avail_stock > 0:
                        deduction = min(current_qty, avail_stock)
                        current_qty = current_qty - deduction
                        stock_info["available_qty"] = max(0.0, avail_stock - deduction)
            return current_qty, actual_stock

        # Step 3: Find Stranding quantity and BOM mapping (with stock deduction applied)
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

                if self.skip_available_sub_assembly_item and selected_wh and prod_item:
                    qty, act_qty = apply_stock_deduction(prod_item, row.get("fg_warehouse"), qty)
                    row.qty = qty
                    row.actual_qty = act_qty
                    row._stock_reduced = True

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

        def to_row_dict(r):
            if hasattr(r, "as_dict") and callable(r.as_dict):
                d = r.as_dict()
            else:
                d = dict(r)
            d.pop("name", None)
            return d

        for row in self.sub_assembly_items:
            fg_wh = (
                row.get("fg_warehouse")
                if hasattr(row, "get")
                else getattr(row, "fg_warehouse", "")
            ) or ""
            fg_wh = str(fg_wh).strip().lower()
            is_buffering = "buffering" in fg_wh

            if not is_buffering or not tube_colors:
                # Non-buffering row (e.g. Stranding, Jacketing)
                if not getattr(row, "_stock_reduced", False) and self.skip_available_sub_assembly_item and selected_wh:
                    prod_item = row.get("production_item") if hasattr(row, "get") else getattr(row, "production_item", None)
                    r_qty = flt(row.get("qty") if hasattr(row, "get") else getattr(row, "qty", 0))
                    r_qty, act_qty = apply_stock_deduction(prod_item, row.get("fg_warehouse"), r_qty)
                    row.qty = r_qty
                    row.actual_qty = act_qty
                    row._stock_reduced = True

                # Only include if remaining qty > 0
                if flt(row.get("qty"), 4) > 0:
                    row_dict = to_row_dict(row)
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

                stranding_qty = None
                if (pp_item, parent_item) in stranding_qty_map:
                    stranding_qty = stranding_qty_map[(pp_item, parent_item)]
                elif parent_item in stranding_qty_map:
                    stranding_qty = stranding_qty_map[parent_item]
                elif pp_item in stranding_qty_map:
                    stranding_qty = stranding_qty_map[pp_item]
                elif "_default" in stranding_qty_map:
                    stranding_qty = stranding_qty_map["_default"]

                orig_qty = flt(row.get("qty") if hasattr(row, "get") else getattr(row, "qty", 0))
                num_colors = len(tube_colors)

                if stranding_qty is not None:
                    target_qty = stranding_qty
                elif num_colors > 0:
                    target_qty = orig_qty / num_colors
                else:
                    target_qty = orig_qty

                # If parent sub-assembly requires 0 (because stock is sufficient), skip buffering items
                if flt(target_qty, 4) <= 0:
                    continue

                row_wh = (row.get("fg_warehouse") or "").strip()

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
                        row_dict = to_row_dict(row)
                        row_dict["custom_tube_colour"] = canonical_color
                        b_qty = target_qty
                        if self.skip_available_sub_assembly_item and selected_wh:
                            b_qty, act_qty = apply_stock_deduction(item_code, row_wh, b_qty)
                            row_dict["actual_qty"] = act_qty
                        row_dict["qty"] = b_qty
                        if flt(row_dict["qty"], 4) > 0:
                            sort_key = tube_color_indices.get(norm_color, 999)
                            buffering_rows_to_sort.append((sort_key, row_dict))
                    # Exclude unselected colors and generic uncolored buffering rows
                else:
                    # Existing flow: duplicate for each selected tube color
                    for color in tube_colors:
                        row_dict = to_row_dict(row)
                        row_dict["custom_tube_colour"] = color
                        b_qty = target_qty
                        item_code = row.get("production_item") if hasattr(row, "get") else getattr(row, "production_item", None)
                        if self.skip_available_sub_assembly_item and selected_wh:
                            b_qty, act_qty = apply_stock_deduction(item_code, row_wh, b_qty)
                            row_dict["actual_qty"] = act_qty
                        row_dict["qty"] = b_qty
                        if flt(row_dict["qty"], 4) > 0:
                            new_sub_assembly_items.append(row_dict)

        # Append sorted buffering rows from BOM-defined colors
        if buffering_rows_to_sort:
            buffering_rows_to_sort.sort(key=lambda x: x[0])
            for sort_idx, row_dict in buffering_rows_to_sort:
                new_sub_assembly_items.append(row_dict)

        # Step 5: Re-assign idx and set back to sub_assembly_items
        self.set("sub_assembly_items", [])
        for idx, row_dict in enumerate(new_sub_assembly_items):
            row_dict["idx"] = idx + 1
            self.append("sub_assembly_items", row_dict)

        if self.skip_available_sub_assembly_item and not self.sub_assembly_items:
            message = (
                _(
                    "As there are sufficient Sub Assembly Items, Work Order is not required for Warehouse {0}."
                ).format(self.sub_assembly_warehouse)
                + "<br><br>"
            )
            message += _(
                "If you still want to proceed, please disable 'Skip Available Sub Assembly Items' checkbox."
            )
            frappe.msgprint(message, title=_("Note"))


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