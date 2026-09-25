import frappe, json


def inspect_wo():
    wo = frappe.get_doc("Work Order", "MFG-WO-2026-00213")
    jc_list = frappe.get_all(
        "Job Card",
        filters={"work_order": wo.name},
        fields=["name", "operation", "for_quantity", "custom_tube_color", "custom_shift", "posting_date"],
    )
    out = {
        "work_order": {
            "name": wo.name,
            "posting_date": str(wo.posting_date) if wo.posting_date else None,
            "custom_customer_name": wo.custom_customer_name,
            "custom_customer_po_no": wo.custom_customer_po_no,
            "custom_sales_order": wo.custom_sales_order,
            "custom_design": wo.custom_design,
            "custom_operation_name": wo.custom_operation_name,
            "custom_shift": wo.custom_shift,
            "production_item": wo.production_item,
            "item_name": wo.item_name,
            "qty": wo.qty,
        },
        "tube_colors": [d.tube_color for d in (wo.custom_tube_color or [])],
        "job_cards": jc_list,
    }
    print(json.dumps(out, indent=2))
