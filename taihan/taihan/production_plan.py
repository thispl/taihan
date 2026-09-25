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

        # Step 1: Map warehouse based on BOM operations if available
        for row in self.sub_assembly_items:
            if row.get("bom_no"):
                bom = frappe.get_doc("BOM", row.get("bom_no"))
                if bom.operations:
                    operation = bom.operations[0].operation
                    warehouse = warehouse_map.get(operation)
                    if warehouse:
                        row.fg_warehouse = warehouse

        # Step 2: Get selected tube colors from Production Plan
        tube_colors = [
            (d.get("tube_color") if hasattr(d, "get") else getattr(d, "tube_color", None))
            for d in self.get("custom_tube_color", [])
            if (d.get("tube_color") if hasattr(d, "get") else getattr(d, "tube_color", None))
        ]

        # Step 3: Duplicate buffering rows based on tube colors
        new_sub_assembly_items = []
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
                for color in tube_colors:
                    row_dict = (
                        row.as_dict()
                        if hasattr(row, "as_dict")
                        else dict(row)
                    )
                    row_dict.pop("name", None)
                    row_dict["custom_tube_colour"] = color
                    new_sub_assembly_items.append(row_dict)

        # Step 4: Re-assign idx and set back to sub_assembly_items
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