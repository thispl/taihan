import frappe


def validate_work_order(doc, method=None):
    if doc.production_plan:
        doc.custom_fiber_count = 12

        # Fetch Tube Colour from Production Plan Sub Assembly table
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

        if tube_color:
            doc.custom_tube_color = tube_color


def before_insert_work_order(doc, method=None):
    validate_work_order(doc, method)


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

        completed_qty = flt(data.completed_qty) + flt(data.process_loss_qty)
        max_allowed = flt(wo_doc.qty)
        pending_qty = max_allowed - max(created_qty, completed_qty)

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
                        "Column Plan quantity must be equal to Manufactured Qty for Operation <b>{0}</b>.<br>Manufactured Qty: <b>{1}</b><br>Column Plan Total: <b>{2}</b>"
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

