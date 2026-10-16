
import frappe
from frappe.model.document import Document
from taihan.taihan.job_card_partial import _append_to_all_batch_nos, _get_produced_qty_for_job_card


def _resolve_employee(value):
    """Return a valid Employee ID. If value is an employee name, look it up."""
    if not value:
        return ""
    if frappe.db.exists("Employee", value):
        return value

    # Normalize whitespace in the supplied value
    normalized = " ".join(str(value).split()).strip().lower()
    for emp in frappe.get_all("Employee", fields=["name", "employee_name"]):
        if " ".join((emp.employee_name or "").split()).strip().lower() == normalized:
            return emp.name

    return value


@frappe.whitelist()
def delete_testing_report(doc,method):
    if frappe.db.exists("Inprocess Testing Report",{"work_order":doc.name}):
        test_report=frappe.get_doc("Inprocess Testing Report",{"work_order":doc.name})
        test_report.delete()



@frappe.whitelist()
def update_tube_color(doc, method):
    if doc.work_order:
        wo = frappe.db.get_value(
            "Work Order",
            doc.work_order,
            ["custom_loose_tube_color", "custom_tube_color", "custom_tube_thickness"],
            as_dict=True,
        )
        if wo:
            need_save = False
            if wo.get("custom_loose_tube_color") and not doc.custom_loose_tube_color:
                doc.custom_loose_tube_color = wo.custom_loose_tube_color
                need_save = True
            if wo.get("custom_tube_color") and not doc.custom_tube_color:
                doc.custom_tube_color = wo.custom_tube_color
                need_save = True
            if wo.get("custom_tube_thickness") and not doc.custom_tube_thickness:
                doc.custom_tube_thickness = wo.custom_tube_thickness
                need_save = True
            if need_save:
                doc.save()


from frappe.utils import flt, get_datetime, time_diff_in_hours


def _ensure_operation_completed_qty(doc, total_produced=0.0):
    """Set Work Order Operation completed_qty high enough so Manufacture Stock Entry validation passes."""
    if not doc.work_order or not doc.operation_id:
        return

    if not total_produced:
        total_produced = flt(doc.total_completed_qty)

    produced_qty = flt(frappe.db.get_value("Work Order", doc.work_order, "produced_qty"))
    target_qty = produced_qty + total_produced
    operation_completed = flt(
        frappe.db.get_value("Work Order Operation", doc.operation_id, "completed_qty")
    )

    if target_qty > operation_completed:
        frappe.db.set_value("Work Order Operation", doc.operation_id, "completed_qty", target_qty)


def _update_work_order_produced_qty(doc, produced_qty=None):
    """Recalculate Work Order produced_qty from all linked Manufacture Stock Entries.

    This is idempotent and does not rely on incrementing a cached/stale value,
    so it recovers if produced_qty was reset or not updated by a previous card."""
    if not doc.work_order:
        return

    if produced_qty is None:
        produced_qty = flt(
            frappe.db.sql(
                """
                SELECT COALESCE(SUM(fg_completed_qty), 0)
                FROM `tabStock Entry`
                WHERE docstatus = 1
                  AND stock_entry_type = "Manufacture"
                  AND (work_order = %s OR custom_work_order = %s)
                """,
                (doc.work_order, doc.work_order),
            )[0][0]
        )

    frappe.db.set_value("Work Order", doc.work_order, "produced_qty", produced_qty)

    if doc.operation_id:
        frappe.db.set_value("Work Order Operation", doc.operation_id, "completed_qty", produced_qty)

    wo_qty = flt(frappe.db.get_value("Work Order", doc.work_order, "qty"))
    if produced_qty >= wo_qty:
        frappe.db.set_value("Work Order", doc.work_order, "status", "Completed")

    # The Stock Entry is linked via custom_work_order, so the standard ERPNext
    # production-plan update is skipped. Trigger it explicitly here.
    wo = frappe.get_doc("Work Order", doc.work_order)
    if wo.production_plan:
        wo.update_production_plan_status()


@frappe.whitelist()
def create_stock_entry(doc, method):

    total_to_produce = flt(doc.total_completed_qty)

    if total_to_produce <= 0:
        frappe.throw("Total produced quantity must be greater than 0.")

    # If the Job Card was already partially produced, only create a stock entry
    # for the remaining quantity.
    produced_so_far = _get_produced_qty_for_job_card(doc.name)
    delta = total_to_produce - produced_so_far

    if delta <= 0:
        # All quantity already produced through partial stock entries
        _update_work_order_produced_qty(doc)
        return

    _ensure_operation_completed_qty(doc, total_to_produce)

    stock = frappe.new_doc("Stock Entry")
    stock.stock_entry_type = "Manufacture"
    # Do not set work_order so ERPNext's overproduction percentage validation is skipped
    stock.custom_work_order = doc.work_order
    stock.company = "TAIHAN KUWAIT FIBER OPTIC  CABLE COMPANY"
    stock.from_bom = 1
    stock.bom_no = doc.bom_no
    stock.fg_completed_qty = delta
    stock.custom_job_card = doc.name

    for_quantity = flt(doc.for_quantity)
    if for_quantity <= 0:
        frappe.throw("For Quantity must be greater than 0 to calculate raw materials.")

    ratio = delta / for_quantity

    for i in doc.items:
        stock.append("items", {
            "item_code": i.item_code,
            "qty": flt(i.required_qty) * ratio,
            "s_warehouse": doc.wip_warehouse or "",
            "t_warehouse": None,
            "is_finished_item": 0
        })

    # Append finished good as the LAST row
    target = frappe.db.get_value("Work Order", doc.work_order, "fg_warehouse")
    if not target:
        frappe.throw("FG Warehouse is not set in Work Order")

    stock.append("items", {
        "item_code": doc.production_item,
        "qty": delta,
        "s_warehouse": None,
        "t_warehouse": target,
        "is_finished_item": 1
    })

    stock.save(ignore_permissions=True)
    stock.submit()

    # Recalculate produced qty from all linked Manufacture Stock Entries.  The Stock
    # Entry created above is linked via custom_work_order, not work_order, so the
    # standard ERPNext produced-qty update is skipped and we do it here.
    _update_work_order_produced_qty(doc)

    batch = frappe.db.get_value("Batch", {"reference_name": stock.name}, "name")
    if not batch:
        batch = frappe.db.get_value("Stock Entry Detail", {"parent": stock.name, "is_finished_item": 1}, "batch_no")

    if batch:
        frappe.db.sql("""
            UPDATE `tabStock Entry Detail`
            SET batch_number = %s, batch_no = %s, custom_batch_qty = %s
            WHERE parent = %s AND is_finished_item = 1
        """, (batch, batch, delta, stock.name))
        frappe.db.sql("""
            UPDATE `tabJob Card`
            SET custom_batch_no = %s, batch_no = %s
            WHERE name = %s
        """, (batch, batch, doc.name))
        doc.custom_batch_no = batch
        doc.batch_no = batch
        _append_to_all_batch_nos(doc, batch)

    frappe.db.sql("""
        UPDATE `tabStock Entry`
        SET job_card = %s
        WHERE name = %s and stock_entry_type = "Manufacture"
    """, (doc.name, stock.name))

    create_pending_material_return(doc)


def create_pending_material_return(doc):
    pending_qty = flt(doc.custom_pending_qty)
    for_quantity = flt(doc.for_quantity)

    if pending_qty <= 0 or for_quantity <= 0:
        return

    if not doc.items:
        return

    existing = frappe.db.exists(
        "Stock Entry",
        {
            "custom_job_card": doc.name,
            "stock_entry_type": "Material Transfer",
            "docstatus": 1,
            "custom_is_excess_entry": ["!=", 1],
        },
    )
    if existing:
        return

    ratio = pending_qty / for_quantity
    wo_source_warehouse = frappe.db.get_value("Work Order", doc.work_order, "source_warehouse") if doc.work_order else None
    default_target_warehouse = wo_source_warehouse or "Stores - TKFOC"

    stock = frappe.new_doc("Stock Entry")
    stock.stock_entry_type = "Material Transfer"
    stock.purpose = "Material Transfer"
    stock.company = "TAIHAN KUWAIT FIBER OPTIC  CABLE COMPANY"
    stock.custom_work_order = doc.work_order
    stock.custom_job_card = doc.name
    stock.from_bom = 0

    items_added = 0
    for i in doc.items:
        item_qty = flt(i.required_qty) * ratio
        if item_qty <= 0:
            continue

        target_wh = i.source_warehouse or default_target_warehouse
        source_wh = doc.wip_warehouse

        has_batch = frappe.db.get_value("Item", i.item_code, "has_batch_no")
        if has_batch:
            batches = get_batch_qty(item_code=i.item_code, warehouse=source_wh) or []
            qty_needed = item_qty
            for b in batches:
                avail_qty = flt(b.get("qty"))
                if avail_qty <= 0:
                    continue
                allocate = min(qty_needed, avail_qty)
                stock.append("items", {
                    "item_code": i.item_code,
                    "qty": allocate,
                    "transfer_qty": allocate,
                    "uom": i.uom or i.stock_uom,
                    "stock_uom": i.stock_uom,
                    "conversion_factor": 1,
                    "s_warehouse": source_wh,
                    "t_warehouse": target_wh,
                    "batch_no": b.get("batch_no"),
                    "is_finished_item": 0,
                })
                qty_needed -= allocate
                items_added += 1
                if qty_needed <= 0:
                    break

            if qty_needed > 0:
                stock.append("items", {
                    "item_code": i.item_code,
                    "qty": qty_needed,
                    "transfer_qty": qty_needed,
                    "uom": i.uom or i.stock_uom,
                    "stock_uom": i.stock_uom,
                    "conversion_factor": 1,
                    "s_warehouse": source_wh,
                    "t_warehouse": target_wh,
                    "is_finished_item": 0,
                })
                items_added += 1
        else:
            stock.append("items", {
                "item_code": i.item_code,
                "qty": item_qty,
                "transfer_qty": item_qty,
                "uom": i.uom or i.stock_uom,
                "stock_uom": i.stock_uom,
                "conversion_factor": 1,
                "s_warehouse": source_wh,
                "t_warehouse": target_wh,
                "is_finished_item": 0,
            })
            items_added += 1

    if items_added > 0:
        stock.save(ignore_permissions=True)
        stock.submit()

        frappe.db.sql("""
            UPDATE `tabStock Entry`
            SET job_card = %s
            WHERE name = %s
        """, (doc.name, stock.name))


@frappe.whitelist()
def create_stock_entry_test(jobcard):
    doc = frappe.get_doc("Job Card", jobcard)
    
    stock = frappe.new_doc("Stock Entry")
    stock.stock_entry_type = "Manufacture"
    stock.work_order = doc.work_order
    stock.company = "TAIHAN KUWAIT FIBER OPTIC  CABLE COMPANY"
    stock.from_bom = 1
    stock.bom_no = doc.bom_no
    stock.fg_completed_qty = doc.total_completed_qty
    stock.custom_job_card = doc.name 
    if doc.operation == "Buffering":  

        for i in doc.items:
            stock.append("items", {
                "item_code": i.item_code,
                "qty": i.required_qty,
                "s_warehouse": doc.wip_warehouse or "",
                "t_warehouse": None,
                "is_finished_item": 0
            })
    elif doc.operation == "Stranding":
        for idx, i in enumerate(doc.items):
    
            stock.append("items", {
                "item_code": i.item_code,
                "qty": i.required_qty,
                "s_warehouse": doc.wip_warehouse or "",
                "t_warehouse": None,
                "is_finished_item": 0
            })
    elif doc.operation == "Jacketing":
        for idx, i in enumerate(doc.items):
        
            stock.append("items", {
                "item_code": i.item_code,
                "qty": i.required_qty,
                "s_warehouse": doc.wip_warehouse or "",
                "t_warehouse": None,
                "is_finished_item": 0
            })


    # 2️⃣ Append finished good as the LAST row
    target = frappe.db.get_value("Work Order", doc.work_order, "fg_warehouse")
    if not target:
        frappe.throw("FG Warehouse is not set in Work Order")

    stock.append("items", {
        "item_code": doc.production_item,
        "qty": doc.total_completed_qty,
        "s_warehouse": None,
        "t_warehouse": target,
        "is_finished_item": 1
    })

    stock.save(ignore_permissions=True)
    # stock.submit()
    batch = frappe.db.get_value("Batch", {"reference_name": stock.name}, "name")
    frappe.db.sql("""
        UPDATE `tabJob Card`
        SET custom_batch_no = %s
        WHERE name = %s
    """, (batch, doc.name))
    frappe.db.sql("""
        UPDATE `tabStock Entry`
        SET job_card = %s
        WHERE work_order = %s and stock_entry_type = "Manufacture" and name=%s
    """, (doc.name, doc.work_order,stock.name))

    if batch:
        _append_to_all_batch_nos(doc, batch)




import frappe

@frappe.whitelist()
def update_excess_qty(job_card, excess_qty, process_loss_qty=None, pending_qty=None):
    doc = frappe.get_doc("Job Card", job_card)
    old_excess = flt(doc.custom_excess_qty)
    new_excess = flt(excess_qty)

    doc.db_set("custom_excess_qty", new_excess)
    if process_loss_qty is not None:
        doc.db_set("process_loss_qty", flt(process_loss_qty))
    if pending_qty is not None:
        doc.db_set("custom_pending_qty", flt(pending_qty))

    if new_excess > old_excess and doc.custom_overproduction_approved:
        doc.db_set("custom_overproduction_approved", 0)
        doc.db_set("custom_overproduction_status", "")

    return True


@frappe.whitelist()
def before_save_job_card(doc, method=None):
    if doc.work_order and not doc.custom_tube_thickness:
        tube_thick = frappe.db.get_value("Work Order", doc.work_order, "custom_tube_thickness")
        if tube_thick:
            doc.custom_tube_thickness = tube_thick

    if doc.name:
        db_process_loss = frappe.db.get_value("Job Card", doc.name, "process_loss_qty")
        if db_process_loss is not None and flt(db_process_loss) != flt(doc.process_loss_qty):
            doc.process_loss_qty = flt(db_process_loss)
        db_pending = frappe.db.get_value("Job Card", doc.name, "custom_pending_qty")
        if db_pending is not None:
            doc.custom_pending_qty = flt(db_pending)

    if doc.docstatus == 1:
        precision = doc.precision("total_completed_qty") or 2
        if doc.items and flt(doc.total_completed_qty, precision) < flt(doc.for_quantity, precision):
            doc.status = "Submitted"
        elif flt(doc.total_completed_qty, precision) >= flt(doc.for_quantity, precision) or not doc.items:
            doc.status = "Completed"
        else:
            doc.status = "Submitted"

    if doc.get("time_logs"):
        creation_dt = get_datetime(doc.creation) if doc.creation else None
        prev_to_time = None
        for idx, d in enumerate(doc.get("time_logs")):
            if idx == 0:
                if creation_dt:
                    d.from_time = creation_dt
            else:
                if prev_to_time:
                    d.from_time = prev_to_time
            if d.from_time and d.to_time:
                d.time_in_mins = time_diff_in_hours(d.to_time, d.from_time) * 60
            prev_to_time = d.to_time

    update_stranding_job_card_items(doc)


@frappe.whitelist()
def sync_submitted_job_card_status(doc, method=None):
    if doc.docstatus == 1:
        precision = doc.precision("total_completed_qty") or 2
        if doc.items and flt(doc.total_completed_qty, precision) < flt(doc.for_quantity, precision):
            doc.db_set("status", "Submitted")
            doc.status = "Submitted"
            if doc.workstation:
                frappe.db.set_value("Workstation", doc.workstation, "status", "Off")
        elif flt(doc.total_completed_qty, precision) >= flt(doc.for_quantity, precision) or not doc.items:
            doc.db_set("status", "Completed")
            doc.status = "Completed"
            if doc.workstation:
                frappe.db.set_value("Workstation", doc.workstation, "status", "Off")
        else:
            doc.db_set("status", "Submitted")
            doc.status = "Submitted"
            if doc.workstation:
                frappe.db.set_value("Workstation", doc.workstation, "status", "Off")


def update_stranding_job_card_items(doc):
    if not doc.work_order:
        return
    if not doc.operation or "stranding" not in str(doc.operation).lower():
        return

    from taihan.taihan.work_order import get_stranding_buffering_items, get_production_plan_tube_colors

    production_plan = frappe.db.get_value("Work Order", doc.work_order, "production_plan")
    if not production_plan:
        return

    tube_colors = get_production_plan_tube_colors(production_plan)
    if not tube_colors:
        return

    bom_no = doc.bom_no or frappe.db.get_value("Work Order", doc.work_order, "bom_no")
    if not bom_no:
        return

    item_color_map, has_tube_colors = get_stranding_buffering_items(bom_no)
    if not item_color_map and not has_tube_colors:
        return

    selected_color_map = {c.lower(): c for c in tube_colors}
    tube_color_indices = {c.lower(): idx for idx, c in enumerate(tube_colors)}

    new_items = []
    buffering_rows_to_sort = []

    for r in doc.get("items", []):
        if r.item_code in item_color_map:
            if has_tube_colors:
                color = item_color_map.get(r.item_code)
                norm_color = color.lower() if color else ""
                if norm_color in selected_color_map:
                    r.required_qty = flt(doc.for_quantity)
                    sort_key = tube_color_indices.get(norm_color, 999)
                    buffering_rows_to_sort.append((sort_key, r))
            else:
                for c in tube_colors:
                    new_r = frappe.copy_doc(r)
                    new_r.required_qty = flt(doc.for_quantity)
                    new_items.append(new_r)
        else:
            new_items.append(r)

    if buffering_rows_to_sort:
        buffering_rows_to_sort.sort(key=lambda x: x[0])
        new_items = [r for _, r in buffering_rows_to_sort] + new_items

    doc.set("items", [])
    for idx, r in enumerate(new_items):
        r.idx = idx + 1
        doc.append("items", r)




@frappe.whitelist()
def create_quality_inspection(doc, method=None, batch_no=None, production_length=None):
    if method is not None:
        doc.reload()
    work_order = frappe.db.get_value("Job Card", doc.name, "work_order")
    qi = frappe.new_doc("Quality Inspection")
    qi.inspection_type = "In Process"
    qi.report_date = frappe.utils.nowdate()
    qi.sales_order = doc.custom_sales_order
    qi.reference_type = "Job Card"
    qi.reference_name = doc.name
    qi.manual_inspection = 1
    qi.item_code = doc.production_item
    if not production_length:
        batch_no_val = batch_no or doc.custom_batch_no
        if batch_no_val:
            production_length = frappe.db.get_value("Batch", batch_no_val, "batch_qty")
    if not production_length:
        production_length = flt(doc.total_completed_qty)
    qi.custom_production_length = flt(production_length)
    qi.sample_size = 1.000
    qi.batch_no = batch_no or doc.custom_batch_no or None
    qi.custom_operator = frappe.db.get_value("Work Order",{"name": work_order}, "custom_operator")
    qi.custom_production_shift_engineering_name = frappe.db.get_value("Work Order",{"name": work_order}, "custom_production_shift_engineering_name")
    qi.custom_production_id = frappe.db.get_value("Work Order",{"name": work_order}, "custom_production_id")
    qi.custom_production_od = frappe.db.get_value("Work Order",{"name": work_order}, "custom_production_od")
    qi.custom_fiber_type = frappe.db.get_value("Work Order",{"name": work_order}, "custom_fiber_type")
    qi.custom_fiber_count = frappe.db.get_value("Work Order",{"name": work_order}, "custom_fiber_count")
    qi.custom_shift = frappe.db.get_value("Work Order",{"name": work_order}, "custom_shift")
    qi.custom_lt_id = frappe.db.get_value("Work Order",{"name": work_order}, "custom_lt_id")
    qi.custom_tube_color= doc.custom_tube_color
    qi.status = "Rejected"

    # get the Operation in Operation Doctype
    qi.quality_inspection_template = frappe.db.get_value(
        "Operation", doc.operation, "quality_inspection_template"
    )


    # # Readings auto fetch from template
    template = qi.quality_inspection_template
    if template:
        template_doc = frappe.get_doc("Quality Inspection Template", template)
        for row in template_doc.item_quality_inspection_parameter:
            qi.append("readings", {
                "specification": row.specification,
                "min_value":row.min_value,
                "max_value":row.max_value
            })

    qi.inspected_by = frappe.session.user

    qi.insert(ignore_permissions=True)
    return qi.name



@frappe.whitelist()
def job_card_print(doc):
    s_no = 1
    product_name=frappe.db.get_value("Item",doc.production_item,"item_name")
    prod_description=frappe.db.get_value("Item",doc.production_item,"description")
    data = '<table border="1" style="border-collapse: collapse; width: 100%;">'
    data += '<tr><td colspan=2 style="text-align:center;background-color: #002060; font-weight:bold;"><span style="color:white;">PRODUCTION ITEM</span></td></tr>'
    data += f'<tr>' \
            f'<td style="text-align:left; font-weight:bold;">Product code</td>' \
            f'<td style="text-align:left;">{doc.production_item}</td>' \
            '</tr>'
    data += f'<tr">' \
            f'<td style="text-align:left; font-weight:bold;">Product Name</td>' \
            f'<td style="text-align:left; ">{product_name}</td>' \
            '</tr>'
    data += f'<tr >' \
            f'<td style="text-align:left; font-weight:bold;">Product Description</td>' \
            f'<td style="text-align:left;">{prod_description}</td>' \
            '</tr>'
    data += f'<tr >' \
            f'<td style="text-align:left; font-weight:bold;">Batch</td>' \
            f'<td style="text-align:left;">{get_all_batches_for_job_card(doc)}</td>' \
            '</tr>'
    data += '</table>'
    data += '<br><br><table border="1" style="border-collapse: collapse; width: 100%;">'
    data += '<tr><td colspan=2 style="text-align:center;background-color: #002060; font-weight:bold;"><span style="color:white;">MACHINE DETAILS</span></td></tr>'
    data += f'<tr>' \
            f'<td style="text-align:left; font-weight:bold;">Operation</td>' \
            f'<td style="text-align:left;">{doc.operation}</td>' \
            '</tr>'
    data += f'<tr">' \
            f'<td style="text-align:left; font-weight:bold;">Workstation Type</td>' \
            f'<td style="text-align:left; ">{doc.workstation_type}</td>' \
            '</tr>'
    data += f'<tr >' \
            f'<td style="text-align:left; font-weight:bold;">Workstation</td>' \
            f'<td style="text-align:left;">{doc.workstation}</td>' \
            '</tr>'
    data += '</table>'
    return data



@frappe.whitelist()
def work_order_print(doc):
    s_no = 1
    product_name=frappe.db.get_value("Item",doc.production_item,"item_name")
    prod_description=frappe.db.get_value("Item",doc.production_item,"description")
    data = '<table border="1" style="border-collapse: collapse; width: 100%;">'
    data += '<tr><td colspan=2 style="text-align:center;background-color: #002060; font-weight:bold;"><span style="color:white;">PRODUCTION ITEM</span></td></tr>'
    data += f'<tr>' \
            f'<td style="text-align:left; font-weight:bold;">Product code</td>' \
            f'<td style="text-align:left;">{doc.production_item}</td>' \
            '</tr>'
    data += f'<tr">' \
            f'<td style="text-align:left; font-weight:bold;">Product Name</td>' \
            f'<td style="text-align:left; ">{product_name}</td>' \
            '</tr>'
    data += f'<tr >' \
            f'<td style="text-align:left; font-weight:bold;">Product Description</td>' \
            f'<td style="text-align:left;">{prod_description}</td>' \
            '</tr>'
    data += '</table>'
    data += '<br><br><table border="1" style="border-collapse: collapse; width: 100%;">'
    data += '<tr><td colspan=5 style="text-align:center; font-weight:bold;"><span">MACHINE DETAILS</span></td></tr>'
    data += f'<tr style="background-color: #002060;">' \
            f'<td style="text-align:center;color:white;">Operation</td>' \
            f'<td style="text-align:center;color:white;">Workstation</td>' \
            f'<td style="text-align:center;color:white;">Status</td>' \
            f'<td style="text-align:center;color:white;">Completed Qty</td>' \
            f'<td style="text-align:center;color:white;">Process Loss Qty</td>' \
            '</tr>'
    for i in doc.operations:
        data += f'<tr >' \
                f'<td style="text-align:left;">{i.operation}</td>' \
                f'<td style="text-align:left;">{i.workstation}</td>' \
                f'<td style="text-align:left;">{i.status}</td>' \
                f'<td style="text-align:right;">{i.completed_qty}</td>' \
                f'<td style="text-align:right;">{i.process_loss_qty}</td>' \
                '</tr>'
    data += '</table>'
    return data



@frappe.whitelist()
def get_batch_values(doc):
    batch_nos = set()  # Using a set to ensure uniqueness

    stock_entries = frappe.get_all("Stock Entry", filters={"docstatus": 1, "work_order": doc.name}, pluck="name")
    
    for entry in stock_entries:
        stock = frappe.get_doc("Stock Entry", entry)
        for item in stock.items:
            if item.batch_no:
                batch_nos.add(item.batch_no)

    return ", ".join(sorted(batch_nos))  # Sorted and comma-separated for display

@frappe.whitelist()
def get_all_batches_for_job_card(doc):
    """Return all Batch IDs created against this Job Card (same Job Card reused for partial production)."""
    job_card_name = doc.name if hasattr(doc, "name") else doc
    batch_nos = set()

    stock_entries = frappe.get_all(
        "Stock Entry",
        filters={
            "docstatus": 1,
            "stock_entry_type": "Manufacture",
            "custom_job_card": job_card_name,
        },
        pluck="name",
    )

    for entry in stock_entries:
        finished_items = frappe.get_all(
            "Stock Entry Detail",
            filters={"is_finished_item": 1, "parent": entry},
            fields=["batch_no"],
        )
        for item in finished_items:
            if item.get("batch_no"):
                batch_nos.add(item.get("batch_no"))

    return ", ".join(sorted(batch_nos))

@frappe.whitelist()
def get_final_batch(doc):
    batch_nos = set()
    stock_entries = frappe.get_all("Stock Entry", filters={"docstatus": 1, "work_order":doc.name}, pluck="name")

    for entry in stock_entries:
        finished_items = frappe.get_all(
            "Stock Entry Detail",
            filters={"is_finished_item": 1, "parent": entry},
            fields=["batch_no"]
        )
        for item in finished_items:
            if item.get("batch_no"):
                batch_nos.add(item.batch_no)

    # print(batch_nos)
    return ", ".join(batch_nos)\





import frappe
from frappe.utils import flt
from erpnext.stock.doctype.batch.batch import get_batch_qty


@frappe.whitelist()
def create_excess_material_transfer(job_card):

    jc = frappe.get_doc("Job Card", job_card)
    wo = frappe.get_doc("Work Order", jc.work_order)

    # Check already created excess material transfer
    existing_entry = frappe.db.get_value(
        "Stock Entry",
        {
            "custom_job_card": jc.name,
            "custom_is_excess_entry": 1,
            "docstatus": ["!=", 2]
        },
        "name"
    )

    if existing_entry:
        return {"existing_entry": existing_entry}


    excess_qty = flt(jc.custom_excess_qty)

    if excess_qty <= 0:
        frappe.throw("No Excess Quantity Found.")

    if not jc.custom_overproduction_approved:
        frappe.throw(
            "Overproduction quantity detected. Approval from an Overproduction Approver is required "
            "before creating excess material transfer."
        )

    bom = frappe.get_doc("BOM", wo.bom_no)

    items = []
    is_stranding = (jc.operation == "Stranding")

    from taihan.taihan.work_order import get_stranding_buffering_items, get_production_plan_tube_colors

    production_plan = wo.production_plan
    tube_colors = get_production_plan_tube_colors(production_plan) if production_plan else []
    selected_color_map = {c.lower(): c for c in tube_colors}
    tube_color_indices = {c.lower(): idx for idx, c in enumerate(tube_colors)}

    item_color_map, has_tube_colors = get_stranding_buffering_items(wo.bom_no) if is_stranding else ({}, False)
    buffering_items_to_sort = []

    for item in bom.items:

        required_qty = (
            flt(item.qty) / flt(bom.quantity)
        ) * excess_qty

        s_warehouse = wo.source_warehouse or "Stores - TKFOC"
        batch_no = ""

        if item.bom_no:
            sub_fg_warehouse = frappe.db.get_value(
                "Work Order",
                {"bom_no": item.bom_no, "docstatus": 1},
                "fg_warehouse"
            )

            if sub_fg_warehouse:
                s_warehouse = sub_fg_warehouse

            completed_jcs = frappe.get_all(
                "Job Card",
                filters={
                    "bom_no": item.bom_no,
                    "docstatus": 1,
                    "status": "Completed"
                },
                fields=["name", "custom_batch_no", "for_quantity", "work_order"]
            )

            for cjc in completed_jcs:
                if frappe.db.get_value("Work Order", cjc.work_order, "production_plan") == \
                   frappe.db.get_value("Work Order", wo.name, "production_plan"):
                    if cjc.custom_batch_no and flt(
                        get_batch_qty(cjc.custom_batch_no, s_warehouse, item.item_code)
                    ) > 0:
                        batch_no = cjc.custom_batch_no
                    else:
                        for b in get_batch_qty(item_code=item.item_code, warehouse=s_warehouse) or []:
                            if flt(b.get("qty")) > 0:
                                batch_no = b.get("batch_no")
                                break
                    break

        if is_stranding and item.item_code in item_color_map:
            if has_tube_colors and tube_colors:
                color = item_color_map.get(item.item_code)
                norm_color = color.lower() if color else ""
                if norm_color in selected_color_map:
                    sort_key = tube_color_indices.get(norm_color, 999)
                    buffering_items_to_sort.append((sort_key, {
                        "item_code": item.item_code,
                        "qty": excess_qty,
                        "transfer_qty": excess_qty,
                        "uom": item.uom,
                        "stock_uom": item.stock_uom,
                        "conversion_factor": item.conversion_factor,
                        "s_warehouse": s_warehouse,
                        "t_warehouse": wo.wip_warehouse,
                        "batch_no": batch_no
                    }))
            elif tube_colors:
                for c in tube_colors:
                    items.append({
                        "item_code": item.item_code,
                        "qty": excess_qty,
                        "transfer_qty": excess_qty,
                        "uom": item.uom,
                        "stock_uom": item.stock_uom,
                        "conversion_factor": item.conversion_factor,
                        "s_warehouse": s_warehouse,
                        "t_warehouse": wo.wip_warehouse,
                        "batch_no": batch_no
                    })
            else:
                fiber_count = flt(jc.custom_fiber_count or wo.custom_fiber_count or 0)
                no_of_tubes = int(fiber_count / 12) if fiber_count else 1
                qty_per_tube = required_qty / no_of_tubes if no_of_tubes > 1 else required_qty
                items.append({
                    "item_code": item.item_code,
                    "qty": qty_per_tube,
                    "transfer_qty": qty_per_tube,
                    "uom": item.uom,
                    "stock_uom": item.stock_uom,
                    "conversion_factor": item.conversion_factor,
                    "s_warehouse": s_warehouse,
                    "t_warehouse": wo.wip_warehouse,
                    "batch_no": batch_no
                })
        else:
            items.append({
                "item_code": item.item_code,
                "qty": required_qty,
                "transfer_qty": required_qty,
                "uom": item.uom,
                "stock_uom": item.stock_uom,
                "conversion_factor": item.conversion_factor,
                "s_warehouse": s_warehouse,
                "t_warehouse": wo.wip_warehouse,
                "batch_no": batch_no
            })

    if buffering_items_to_sort:
        buffering_items_to_sort.sort(key=lambda x: x[0])
        items = [x[1] for x in buffering_items_to_sort] + items

    return {
        "stock_entry_type": "Material Transfer for Manufacture",
        "purpose": "Material Transfer for Manufacture",
        "company": wo.company,
        "work_order": wo.name,
        "custom_work_order": wo.name,
        "custom_is_excess_entry": 1,
        "custom_job_card": jc.name,
        "from_bom": 1,
        "bom_no": wo.bom_no,
        "fg_completed_qty": excess_qty,
        "items": items
    }






@frappe.whitelist()
def validate_excess_material_transfer(doc, method=None):
    excess_qty = flt(doc.custom_excess_qty)

    if excess_qty > 0:
        if not (doc.custom_overproduction_approved or doc.custom_overproduction_status == "Approved"):
            frappe.throw(
                "Excess quantity is available. Please get Arif Sir's approval before submitting the Job Card."
            )

        existing_entry = frappe.db.exists(
            "Stock Entry",
            {
                "custom_work_order": doc.work_order,
                "custom_is_excess_entry": 1,
                "docstatus": 1
            }
        )

        if not existing_entry:
            frappe.throw(
                "Excess quantity is available. Please create Excess Material Transfer before submitting the Job Card."
            )


@frappe.whitelist()
def request_overproduction_approval(job_card, remarks=None):
    jc = frappe.get_doc("Job Card", job_card)
    if flt(jc.custom_excess_qty) <= 0:
        frappe.throw("No excess quantity to approve")
    jc.db_set("custom_overproduction_status", "Pending")
    if remarks:
        jc.db_set("custom_overproduction_remarks", remarks)
    frappe.db.commit()
    return {"message": "Requested approval", "job_card": job_card}


@frappe.whitelist()
def approve_overproduction(job_card, remarks=None):
    user = frappe.session.user
    allowed = (user == "arif@taihankw.com") or ("Overproduction Approver" in frappe.get_roles(user))
    if not allowed:
        frappe.throw("Only Arif Sir can approve overproduction.", title="Not Permitted")
    return _set_approval_status(job_card, "Approved", remarks)


@frappe.whitelist()
def reject_overproduction(job_card, remarks):
    user = frappe.session.user
    allowed = (user == "arif@taihankw.com") or ("Overproduction Approver" in frappe.get_roles(user))
    if not allowed:
        frappe.throw("Only Arif Sir can reject overproduction.", title="Not Permitted")
    if not remarks:
        frappe.throw("Rejection reason is required")
    return _set_approval_status(job_card, "Rejected", remarks)


@frappe.whitelist()
def approve_job_card_overproduction(job_card, remarks=None):
    user = frappe.session.user
    allowed = (user == "arif@taihankw.com") or ("Overproduction Approver" in frappe.get_roles(user))
    if not allowed:
        frappe.throw("Only Arif Sir can approve overproduction.", title="Not Permitted")
    jc = frappe.get_doc("Job Card", job_card)
    jc.db_set("custom_overproduction_approved", 1)
    jc.db_set("custom_overproduction_status", "Approved")
    jc.db_set("custom_approved_by", user)
    jc.db_set("custom_approval_date", frappe.utils.now())
    if remarks:
        jc.db_set("custom_overproduction_remarks", remarks)
    frappe.db.commit()
    return {"message": "Approved", "job_card": job_card}


def _set_approval_status(job_card, status, remarks):
    jc = frappe.get_doc("Job Card", job_card)
    jc.db_set("custom_overproduction_status", status)
    jc.db_set("custom_approved_by", frappe.session.user)
    jc.db_set("custom_approval_date", frappe.utils.now())
    if remarks:
        jc.db_set("custom_overproduction_remarks", remarks)
    if status == "Approved":
        jc.db_set("custom_overproduction_approved", 1)
    else:
        jc.db_set("custom_overproduction_approved", 0)
    frappe.db.commit()
    return {"message": status, "job_card": job_card}


@frappe.whitelist()
def _create_excess_material_transfer_duplicate(job_card):
    doc = frappe.get_doc("Job Card", job_card)
    if not (doc.custom_overproduction_approved or doc.custom_overproduction_status == "Approved"):
        frappe.throw("Overproduction is not approved. Kindly get Approval First.")
    excess_qty = flt(doc.custom_excess_qty)
    for_quantity = flt(doc.for_quantity)
    if excess_qty <= 0:
        frappe.throw("Excess quantity must be greater than 0")
    if for_quantity <= 0:
        frappe.throw("For Quantity must be greater than 0")
    if not doc.wip_warehouse:
        frappe.throw("WIP Warehouse is not set in Job Card")

    existing = frappe.db.get_value("Stock Entry", {
        "custom_job_card": doc.name,
        "custom_is_excess_entry": 1,
        "docstatus": 1
    }, "name")
    if existing:
        return {"existing_entry": existing}

    ratio = excess_qty / for_quantity
    items = []
    for item in doc.items:
        if not item.source_warehouse:
            frappe.throw("Source warehouse is required for item {0}".format(item.item_code))
        qty = flt(item.required_qty) * ratio
        uom = item.uom or item.stock_uom
        items.append({
            "item_code": item.item_code,
            "qty": qty,
            "transfer_qty": qty,
            "uom": uom,
            "stock_uom": item.stock_uom,
            "conversion_factor": 1,
            "s_warehouse": item.source_warehouse,
            "t_warehouse": doc.wip_warehouse,
            "batch_no": "",
        })

    return {
        "stock_entry_type": "Material Transfer for Manufacture",
        "purpose": "Material Transfer for Manufacture",
        "company": doc.company,
        "work_order": doc.work_order,
        "custom_work_order": doc.work_order,
        "custom_is_excess_entry": 1,
        "custom_job_card": doc.name,
        "from_bom": 0,
        "bom_no": doc.bom_no,
        "fg_completed_qty": excess_qty,
        "items": items
    }


@frappe.whitelist()
def create_excess_stock_entry(job_card):
    doc = frappe.get_doc("Job Card", job_card)
    if not (doc.custom_overproduction_approved or doc.custom_overproduction_status == "Approved"):
        frappe.throw("Overproduction is not approved. Please get Arif Sir's approval first.")
    excess_qty = flt(doc.custom_excess_qty)
    for_quantity = flt(doc.for_quantity)
    if excess_qty <= 0:
        frappe.throw("Excess quantity must be greater than 0")
    if for_quantity <= 0:
        frappe.throw("For Quantity must be greater than 0")
    if not doc.wip_warehouse:
        frappe.throw("WIP Warehouse is not set in Job Card")

    existing_entry = frappe.db.get_value(
        "Stock Entry",
        {
            "custom_work_order": doc.work_order,
            "custom_is_excess_entry": 1,
            "docstatus": 1
        },
        "name"
    )
    if existing_entry:
        frappe.msgprint(frappe._("Excess Material Transfer {0} already exists and is submitted.").format(existing_entry))
        return {"name": existing_entry}

    stock = frappe.new_doc("Stock Entry")
    stock.stock_entry_type = "Material Transfer"
    stock.purpose = "Material Transfer"
    stock.company = doc.company
    stock.custom_work_order = doc.work_order
    stock.custom_job_card = doc.name
    stock.custom_is_excess_entry = 1

    if doc.operation == "Stranding":
        wo = frappe.get_doc("Work Order", doc.work_order)
        fiber_count = flt(wo.custom_fiber_count)
        if fiber_count <= 0:
            frappe.throw("Fiber Count is not set in Work Order")

        tube_count = int(fiber_count / 12)
        if tube_count <= 0:
            tube_count = 1

        item_code = doc.production_item
        s_warehouse = frappe.db.get_value("Work Order", doc.work_order, "fg_warehouse") or "Buffering - TKFOC"
        t_warehouse = doc.wip_warehouse

        all_batches = [b.strip() for b in (doc.custom_all_batch_nos or "").split(",") if b.strip()]
        if not all_batches:
            all_batches = [doc.custom_batch_no] if doc.custom_batch_no else []

        from erpnext.stock.doctype.batch.batch import get_batch_qty

        uom = frappe.db.get_value("Item", item_code, "stock_uom")
        qty_per_tube = flt(excess_qty) / tube_count
        lines_added = 0

        for batch in all_batches:
            if lines_added >= tube_count:
                break
            batch_qty = get_batch_qty(batch, s_warehouse, item_code) or 0
            if batch_qty <= 0:
                continue
            qty = min(flt(batch_qty), qty_per_tube)
            stock.append("items", {
                "item_code": item_code,
                "qty": qty,
                "uom": uom,
                "stock_uom": uom,
                "conversion_factor": 1,
                "s_warehouse": s_warehouse,
                "t_warehouse": t_warehouse,
                "batch_no": batch,
            })
            lines_added += 1

        # Fallback: if the Job Card's batches are not in the source warehouse,
        # pick any batch that is actually available in the buffering warehouse.
        if not stock.get("items"):
            available_batches = get_batch_qty(item_code=item_code, warehouse=s_warehouse) or []
            for batch in available_batches:
                if lines_added >= tube_count:
                    break
                batch_qty = flt(batch.get("qty"))
                if batch_qty <= 0:
                    continue
                qty = min(batch_qty, qty_per_tube)
                stock.append("items", {
                    "item_code": item_code,
                    "qty": qty,
                    "uom": uom,
                    "stock_uom": uom,
                    "conversion_factor": 1,
                    "s_warehouse": s_warehouse,
                    "t_warehouse": t_warehouse,
                    "batch_no": batch.get("batch_no"),
                })
                lines_added += 1

        if not stock.get("items"):
            frappe.throw("No available batch balance found in buffering warehouse for the excess material transfer.")
    else:
        ratio = excess_qty / for_quantity
        for item in doc.items:
            if not item.source_warehouse:
                frappe.throw("Source warehouse is required for item {0}".format(item.item_code))
            stock.append("items", {
                "item_code": item.item_code,
                "qty": flt(item.required_qty) * ratio,
                "uom": item.uom or item.stock_uom,
                "s_warehouse": item.source_warehouse,
                "t_warehouse": doc.wip_warehouse,
            })

    stock.save(ignore_permissions=True)
    stock.submit()
    frappe.db.commit()

    return {"name": stock.name}


def get_barcode_svg(value, barcode_type="Code128"):
    """Return a base64-encoded SVG barcode image for the given value (no built-in text)."""
    if not value:
        return ""
    try:
        import base64
        from io import BytesIO
        from barcode import get_barcode_class
        from barcode.writer import SVGWriter

        barcode_class = get_barcode_class(barcode_type)
        buffer = BytesIO()
        barcode_class(str(value), writer=SVGWriter()).write(
            buffer,
            options={"write_text": False, "module_height": 8, "quiet_zone": 2}
        )
        encoded = base64.b64encode(buffer.getvalue()).decode()
        return "data:image/svg+xml;base64," + encoded
    except Exception:
        return ""


def get_barcode_img(value, height=10, barcode_type="Code128"):
    """Return an <img> tag with a base64 SVG barcode."""
    svg = get_barcode_svg(value, barcode_type)
    if not svg:
        return ""
    return f'<img src="{svg}" style="height:{float(height)}mm; width:auto; display:block; margin:0 auto;" />'


@frappe.whitelist()
def get_job_cards_for_work_order(work_order):
    """Return Job Cards linked to a Work Order for printing."""
    if not work_order:
        return []
    cards = frappe.get_all(
        "Job Card",
        filters={"work_order": work_order},
        fields=[
            "name",
            "operation",
            "for_quantity",
            "custom_tube_color",
            "custom_shift",
            "posting_date",
            "custom_production_incharge",
            "status",
        ],
        order_by="name asc",
    )
    for card in cards:
        engineer = ""
        if card.get("custom_production_incharge"):
            engineer = frappe.db.get_value(
                "Employee", card.custom_production_incharge, "employee_name"
            )
        card["engineer_name"] = engineer
        card["posting_date"] = (
            frappe.utils.format_date(card.posting_date, "dd-MM-yyyy")
            if card.get("posting_date")
            else ""
        )
    return cards


def ensure_overproduction_approval_fields():
    """Ensure custom fields and fix status on submitted Job Cards."""
    frappe.db.sql("""
        UPDATE `tabJob Card`
        SET status = 'Submitted'
        WHERE docstatus = 1
          AND status = 'Work In Progress'
          AND for_quantity != total_completed_qty
    """)
    frappe.db.commit()

