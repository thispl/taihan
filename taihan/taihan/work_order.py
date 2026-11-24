import frappe


def get_work_order_process_type(doc):
    """Detect if Work Order is Buffering, Stranding, or Jacketing."""
    candidates = []
    if getattr(doc, "custom_operation_name", None):
        candidates.append(str(doc.custom_operation_name))

    if getattr(doc, "operations", None):
        for op in doc.operations:
            if getattr(op, "operation", None):
                candidates.append(str(op.operation))

    if getattr(doc, "bom_no", None):
        bom_ops = frappe.get_all(
            "BOM Operation",
            filters={"parent": doc.bom_no},
            fields=["operation"],
            order_by="idx asc",
        )
        for b_op in bom_ops:
            if b_op.operation:
                candidates.append(str(b_op.operation))

    if getattr(doc, "fg_warehouse", None):
        candidates.append(str(doc.fg_warehouse))

    if getattr(doc, "production_plan_sub_assembly_item", None):
        sub_item = frappe.db.get_value(
            "Production Plan Sub Assembly Item",
            doc.production_plan_sub_assembly_item,
            ["fg_warehouse", "custom_tube_colour"],
            as_dict=True,
        )
        if sub_item:
            if sub_item.fg_warehouse:
                candidates.append(str(sub_item.fg_warehouse))
            if sub_item.custom_tube_colour:
                candidates.append("Buffering")

    for c in candidates:
        low = c.lower()
        if "buffering" in low:
            return "Buffering"
        elif "stranding" in low:
            return "Stranding"
        elif "jacketing" in low or "sheathing" in low:
            return "Jacketing"

    return None


def validate_work_order(doc, method=None):
    process_type = get_work_order_process_type(doc)
    if process_type and not doc.custom_operation_name:
        doc.custom_operation_name = process_type

    if doc.production_plan:
        doc.custom_fiber_count = frappe.db.get_value(
            "Production Plan", doc.production_plan, "custom_fiber_count"
        )
        if doc.custom_operation_name == "Buffering" or process_type == "Buffering":
            doc.custom_fiber_count = 12

        pp_tube_colors = get_production_plan_tube_colors(doc.production_plan)

        if process_type in ("Stranding", "Jacketing"):
            # If Stranding or Jacketing -> Tube Color should be set to all colors updated in Production Plan
            if pp_tube_colors:
                existing_colors = [
                    d.tube_color
                    for d in doc.get("custom_tube_color", [])
                    if getattr(d, "tube_color", None)
                ]
                if not existing_colors or doc.is_new():
                    doc.set("custom_tube_color", [])
                    for color in pp_tube_colors:
                        doc.append("custom_tube_color", {"tube_color": color})

        elif process_type == "Buffering":
            # If Buffering then update only one color per Work Order
            tube_color = None
            if doc.production_plan_sub_assembly_item:
                tube_color = frappe.db.get_value(
                    "Production Plan Sub Assembly Item",
                    doc.production_plan_sub_assembly_item,
                    "custom_tube_colour",
                )
            elif doc.production_item:
                tube_color = frappe.db.get_value(
                    "Production Plan Sub Assembly Item",
                    {
                        "parent": doc.production_plan,
                        "production_item": doc.production_item,
                    },
                    "custom_tube_colour",
                )

            if not tube_color and doc.production_item:
                tube_color = frappe.db.get_value("Item", doc.production_item, "custom_tube_colour")

            if tube_color:
                existing_colors = [
                    d.tube_color
                    for d in doc.get("custom_tube_color", [])
                    if getattr(d, "tube_color", None)
                ]
                if not existing_colors or existing_colors != [tube_color] or doc.is_new():
                    doc.set("custom_tube_color", [])
                    doc.append("custom_tube_color", {"tube_color": tube_color})

    if doc.operations:
        seq_id = 0
        for operation in doc.operations:
            operation.sequence_id = seq_id + 1
            seq_id += 1

    update_stranding_work_order_required_items(doc)


def before_insert_work_order(doc, method=None):
    validate_work_order(doc, method)


def ensure_tube_color_custom_field():
    """Ensure custom_tube_color on Work Order is Table MultiSelect pointing to Tube Color Child."""
    cf_name = "Work Order-custom_tube_color"
    needs_recreate = False
    if frappe.db.exists("Custom Field", cf_name):
        cf = frappe.get_doc("Custom Field", cf_name)
        if cf.fieldtype != "Table MultiSelect" or cf.options != "Tube Color Child" or cf.depends_on:
            frappe.delete_doc("Custom Field", cf_name, force=True)
            needs_recreate = True
    else:
        needs_recreate = True

    if needs_recreate:
        cf_doc = frappe.new_doc("Custom Field")
        cf_doc.dt = "Work Order"
        cf_doc.fieldname = "custom_tube_color"
        cf_doc.label = "Tube Color"
        cf_doc.fieldtype = "Table MultiSelect"
        cf_doc.options = "Tube Color Child"
        cf_doc.insert_after = "custom_fiber_count"
        cf_doc.insert(ignore_permissions=True)
        frappe.clear_cache(doctype="Work Order")

    # Migrate any existing values in tabWork Order.custom_tube_color to tabTube Color Child
    try:
        existing_rows = frappe.db.sql("""
            SELECT name, custom_tube_color
            FROM `tabWork Order`
            WHERE custom_tube_color IS NOT NULL AND custom_tube_color != ''
        """, as_dict=True)
        for row in existing_rows:
            has_child = frappe.db.exists("Tube Color Child", {
                "parent": row.name,
                "parenttype": "Work Order",
                "parentfield": "custom_tube_color"
            })
            if not has_child and row.custom_tube_color:
                frappe.get_doc({
                    "doctype": "Tube Color Child",
                    "parent": row.name,
                    "parenttype": "Work Order",
                    "parentfield": "custom_tube_color",
                    "tube_color": row.custom_tube_color,
                    "idx": 1
                }).insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception:
        pass


def get_stranding_buffering_items(bom_no):
    if not bom_no:
        return {}, False
    bom_items = frappe.get_all(
        "BOM Item",
        filters={"parent": bom_no},
        fields=["item_code", "bom_no", "custom_tube_colour"],
    )
    item_color_map = {}
    has_tube_colors = False
    for bi in bom_items:
        if bi.bom_no:
            bom_ops = frappe.get_all(
                "BOM Operation",
                filters={"parent": bi.bom_no},
                fields=["operation"],
                order_by="idx asc",
                limit=1,
            )
            op = bom_ops[0].operation if bom_ops else ""
            if op and op.lower() == "buffering":
                color = bi.custom_tube_colour or frappe.db.get_value(
                    "Item", bi.item_code, "custom_tube_colour"
                )
                if color:
                    item_color_map[bi.item_code] = str(color).strip()
                    has_tube_colors = True
                else:
                    item_color_map[bi.item_code] = None
    return item_color_map, has_tube_colors


@frappe.whitelist()
def get_production_plan_tube_colors(production_plan):
    if not production_plan:
        return []
    return [
        str(d.tube_color).strip()
        for d in frappe.get_all(
            "Tube Color Child",
            filters={"parent": production_plan, "parenttype": "Production Plan"},
            fields=["tube_color"],
            order_by="idx asc",
        )
        if d.tube_color
    ]


def update_stranding_work_order_required_items(doc):
    if not doc.bom_no or not doc.production_plan:
        return

    is_stranding = False
    if doc.custom_operation_name and "stranding" in str(doc.custom_operation_name).lower():
        is_stranding = True
    elif doc.operations:
        for op in doc.operations:
            if op.operation and "stranding" in str(op.operation).lower():
                is_stranding = True
                break
    else:
        bom_ops = frappe.get_all("BOM Operation", filters={"parent": doc.bom_no}, fields=["operation"])
        for op in bom_ops:
            if op.operation and "stranding" in str(op.operation).lower():
                is_stranding = True
                break

    if not is_stranding:
        return

    tube_colors = get_production_plan_tube_colors(doc.production_plan)
    if not tube_colors:
        return

    item_color_map, has_tube_colors = get_stranding_buffering_items(doc.bom_no)
    if not item_color_map and not has_tube_colors:
        return

    selected_color_map = {c.lower(): c for c in tube_colors}
    tube_color_indices = {c.lower(): idx for idx, c in enumerate(tube_colors)}

    new_required_items = []
    buffering_rows_to_sort = []

    for r in doc.get("required_items", []):
        if r.item_code in item_color_map:
            if has_tube_colors:
                color = item_color_map.get(r.item_code)
                norm_color = color.lower() if color else ""
                if norm_color in selected_color_map:
                    r.required_qty = flt(doc.qty)
                    sort_key = tube_color_indices.get(norm_color, 999)
                    buffering_rows_to_sort.append((sort_key, r))
            else:
                for c in tube_colors:
                    new_r = frappe.copy_doc(r)
                    new_r.required_qty = flt(doc.qty)
                    new_required_items.append(new_r)
        else:
            new_required_items.append(r)

    if buffering_rows_to_sort:
        buffering_rows_to_sort.sort(key=lambda x: x[0])
        new_required_items = [r for _, r in buffering_rows_to_sort] + new_required_items

    doc.set("required_items", [])
    for idx, r in enumerate(new_required_items):
        r.idx = idx + 1
        doc.append("required_items", r)


import json
from frappe import _
from frappe.utils import flt, nowdate, get_link_to_form


@frappe.whitelist()
def get_operations_for_job_card_dialog(work_order):
    wo_doc = frappe.get_doc("Work Order", work_order)
    pending_operations = []

    for data in wo_doc.operations:
        # Sum for_quantity of all active Job Cards already created for this operation
        created_qty = flt(
            frappe.db.sql(
                """
                SELECT COALESCE(SUM(for_quantity), 0)
                FROM `tabJob Card`
                WHERE docstatus < 2
                  AND work_order = %s
                  AND (operation_id = %s OR (operation = %s AND sequence_id = %s))
                """,
                (wo_doc.name, data.name, data.operation, data.sequence_id or 1),
            )[0][0]
        )

        pending_qty = flt(wo_doc.qty) - flt(data.completed_qty) - flt(data.process_loss_qty)

        if pending_qty > 0:
            pending_operations.append({
                "name": data.name,
                "operation": data.operation,
                "workstation": data.workstation or "",
                "sequence_id": data.sequence_id or 1,
                "batch_size": data.batch_size or 0,
                "workstation_type": data.workstation_type or "",
                "hour_rate": data.hour_rate or 0,
                "pending_qty": pending_qty,
                "qty": pending_qty,
                "created_jc_qty": created_qty,
                "use_column_plan": False,
                "no_of_job_cards": None,
                "column_quantities": [],
            })

    return pending_operations


@frappe.whitelist()
def make_job_cards_with_column_plan(work_order, operations):
    if isinstance(operations, str):
        operations = json.loads(operations)

    wo_doc = frappe.get_doc("Work Order", work_order)
    created_job_cards = []

    from erpnext.manufacturing.doctype.work_order.work_order import (
        create_job_card as erpnext_create_job_card,
        make_job_card as erpnext_make_job_card,
    )

    for op in operations:
        op = frappe._dict(op)
        op_row = None
        for d in wo_doc.operations:
            if d.name == op.name or (d.operation == op.operation and d.sequence_id == op.sequence_id):
                op_row = d
                break

        if not op_row:
            continue

        if op.get("use_column_plan") and op.get("column_quantities"):
            col_qtys = [flt(q) for q in op.get("column_quantities")]
            total_col_qty = sum(col_qtys)
            expected_qty = flt(op.get("qty"))

            if abs(total_col_qty - expected_qty) > 0.001:
                frappe.throw(
                    _(
                        "Plan quantity must be equal to Creatable Job Card Qty for Operation <b>{0}</b>.<br>Creatable Job Card Qty: <b>{1}</b><br>Plan Total: <b>{2}</b>"
                    ).format(op_row.operation, expected_qty, total_col_qty)
                )

            for col_qty in col_qtys:
                if col_qty <= 0:
                    continue
                row_data = frappe._dict(op_row.as_dict())
                row_data.job_card_qty = col_qty
                row_data.operation_id = op_row.name
                jc = erpnext_create_job_card(wo_doc, row_data, auto_create=True)
                if jc and getattr(jc, "name", None):
                    created_job_cards.append(jc.name)
        else:
            qty = flt(op.get("qty"))
            if qty > 0:
                erpnext_make_job_card(work_order, [op])

    return created_job_cards

