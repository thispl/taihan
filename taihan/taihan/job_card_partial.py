import frappe
from frappe.utils import flt


def _get_produced_qty_for_job_card(job_card_name):
    """Return the total FG quantity already produced for this Job Card."""
    return flt(
        frappe.db.sql(
            """
            SELECT COALESCE(SUM(fg_completed_qty), 0)
            FROM `tabStock Entry`
            WHERE docstatus = 1
              AND stock_entry_type = "Manufacture"
              AND (custom_job_card = %s OR job_card = %s)
            """,
            (job_card_name, job_card_name),
        )[0][0]
    )


def _get_batch_produced_qty(job_card_name, batch_no):
    """Return the finished quantity produced for a specific batch on a Job Card."""
    return flt(
        frappe.db.sql(
            """
            SELECT COALESCE(SUM(sed.qty), 0)
            FROM `tabStock Entry Detail` sed
            INNER JOIN `tabStock Entry` se ON se.name = sed.parent
            WHERE se.docstatus = 1
              AND se.stock_entry_type = "Manufacture"
              AND (se.custom_job_card = %s OR se.job_card = %s)
              AND sed.is_finished_item = 1
              AND sed.batch_no = %s
            """,
            (job_card_name, job_card_name, batch_no),
        )[0][0]
    )


def _get_batches_for_job_card(job_card_name):
    """Return all finished batches and their produced quantities for a Job Card."""
    rows = frappe.db.sql(
        """
        SELECT sed.batch_no, SUM(sed.qty) as qty
        FROM `tabStock Entry Detail` sed
        INNER JOIN `tabStock Entry` se ON se.name = sed.parent
        WHERE se.docstatus = 1
          AND se.stock_entry_type = "Manufacture"
          AND (se.custom_job_card = %s OR se.job_card = %s)
          AND sed.is_finished_item = 1
          AND sed.batch_no IS NOT NULL
          AND sed.batch_no != ''
        GROUP BY sed.batch_no
        ORDER BY se.posting_date, se.posting_time, se.creation
        """,
        (job_card_name, job_card_name),
        as_dict=True,
    )
    return rows


def _ensure_all_batch_nos_field():
	"""Create or update the custom_all_batch_nos field on Job Card."""
	cf_name = frappe.db.get_value(
		"Custom Field", {"dt": "Job Card", "fieldname": "custom_all_batch_nos"}, "name"
	)
	if cf_name:
		cf = frappe.get_doc("Custom Field", cf_name)
	else:
		cf = frappe.new_doc("Custom Field")
		cf.dt = "Job Card"
		cf.fieldname = "custom_all_batch_nos"
		cf.insert_after = "custom_batch_no"

	cf.label = "All Batch Numbers"
	cf.fieldtype = "Data"
	cf.read_only = 1
	cf.hidden = 0
	cf.save(ignore_permissions=True)
	frappe.clear_cache(doctype="Job Card")


def _append_to_all_batch_nos(doc, batch):
	"""Append a batch number to the Job Card's all-batch history.

	The field is created lazily; if the column does not exist yet (e.g. before
	bench migrate), the write is skipped without error. All batches can still be
	read from the linked Manufacture Stock Entries via get_all_batches_for_job_card.
	"""
	_ensure_all_batch_nos_field()

	if not frappe.db.has_column("Job Card", "custom_all_batch_nos"):
		return

	doc.reload()
	existing = doc.get("custom_all_batch_nos") or ""
	if existing and batch in [b.strip() for b in existing.split(",")]:
		return
	doc.custom_all_batch_nos = (existing + ", " + batch) if existing else batch
	doc.db_set("custom_all_batch_nos", doc.custom_all_batch_nos)


def _make_stock_entry(doc, fg_completed_qty, finished_item_qty, raw_material_ratio=1.0):
    """Create and submit a Manufacture Stock Entry for the given quantities."""

    stock = frappe.new_doc("Stock Entry")
    stock.stock_entry_type = "Manufacture"
    stock.purpose = "Manufacture"
    # Do not set work_order directly so ERPNext's cumulative process loss and overproduction validations are skipped
    stock.custom_work_order = doc.work_order
    stock.company = "TAIHAN KUWAIT FIBER OPTIC  CABLE COMPANY"
    stock.from_bom = 1
    stock.bom_no = doc.bom_no
    stock.fg_completed_qty = fg_completed_qty
    stock.custom_job_card = doc.name
    stock.process_loss_qty = 0.0
    stock.process_loss_percentage = 0.0

    for i in doc.items:
        stock.append("items", {
            "item_code": i.item_code,
            "qty": flt(i.required_qty) * raw_material_ratio,
            "s_warehouse": doc.wip_warehouse or "",
            "t_warehouse": None,
            "is_finished_item": 0
        })

    target = frappe.db.get_value("Work Order", doc.work_order, "fg_warehouse")
    if not target:
        frappe.throw("FG Warehouse is not set in Work Order")

    stock.append("items", {
        "item_code": doc.production_item,
        "qty": finished_item_qty,
        "s_warehouse": None,
        "t_warehouse": target,
        "is_finished_item": 1
    })

    stock.save(ignore_permissions=True)
    stock.submit()

    batch = frappe.db.get_value("Batch", {"reference_name": stock.name}, "name")
    if not batch:
        batch = frappe.db.get_value("Stock Entry Detail", {"parent": stock.name, "is_finished_item": 1}, "batch_no")

    if batch:
        frappe.db.sql("""
            UPDATE `tabStock Entry Detail`
            SET batch_number = %s, batch_no = %s, custom_batch_qty = %s
            WHERE parent = %s AND is_finished_item = 1
        """, (batch, batch, finished_item_qty, stock.name))

    frappe.db.sql("""
        UPDATE `tabStock Entry`
        SET job_card = %s
        WHERE name = %s and stock_entry_type = "Manufacture"
    """, (doc.name, stock.name))

    return stock.name, batch


@frappe.whitelist()
def create_partial_stock_entry(job_card):
    """Complete a partial production run and keep using the same Job Card.

    A Manufacture Stock Entry (and its Batch) is created for the completed
    quantity. The same Job Card is then reset to the remaining quantity so it
    can be used again when the balance is produced later.
    """
    doc = frappe.get_doc("Job Card", job_card)

    if doc.docstatus != 0:
        frappe.throw("Job Card must be in Draft status.")

    if not doc.get("time_logs"):
        frappe.throw("Please add time logs with the completed quantity before proceeding.")

    completed_qty = flt(doc.total_completed_qty)
    for_quantity = flt(doc.for_quantity)

    if completed_qty <= 0 or completed_qty >= for_quantity:
        frappe.throw("Completed quantity must be greater than 0 and less than For Quantity.")

    # Only produce the quantity that has not been produced yet (delta).
    produced_so_far = _get_produced_qty_for_job_card(doc.name)
    delta = completed_qty - produced_so_far
    if delta <= 0:
        frappe.throw("This quantity has already been produced through a previous partial stock entry.")

    partial_ratio = delta / for_quantity

    # Pre-update the Work Order Operation so the Manufacture Stock Entry validation passes.
    # After the Stock Entry is submitted, Work Order.produced_qty will be the source of truth.
    if doc.work_order and doc.operation_id:
        operation_completed = flt(
            frappe.db.get_value("Work Order Operation", doc.operation_id, "completed_qty")
        )
        frappe.db.set_value(
            "Work Order Operation",
            doc.operation_id,
            "completed_qty",
            operation_completed + delta,
        )

    # Create stock entry (and Batch) for the newly completed portion
    stock_name, batch = _make_stock_entry(doc, delta, delta, partial_ratio)

    from taihan.taihan.job_card import _update_work_order_produced_qty
    _update_work_order_produced_qty(doc)

    # Keep for_quantity and required_qty at their original values.
    # total_completed_qty is recalculated from time logs during save and will reflect
    # the cumulative completed qty (including this partial run). This ensures
    # for_quantity > total_completed_qty remains true so the Start Job button shows.
    doc.total_time_in_mins = 0.0
    doc.process_loss_qty = 0.0

    # Reset timer fields so the Start Job button is available for the next partial run
    doc.started_time = None
    doc.current_time = 0

    # Clear all child tables except time_logs, which the user wants to see
    for table in ["employee", "scheduled_time_logs", "scrap_items", "sub_operations"]:
        doc.set(table, [])

    doc.custom_batch_no = batch
    doc.quality_inspection = None
    doc.serial_and_batch_bundle = None
    doc.batch_no = None
    doc.serial_no = None

    doc.save(ignore_permissions=True)

    _append_to_all_batch_nos(doc, batch)

    # Create a Quality Inspection for this partial batch
    if batch:
        from taihan.taihan.job_card import create_quality_inspection
        create_quality_inspection(doc, batch_no=batch, production_length=delta)

    # set_process_loss may have re-set this to the remaining planned qty; reset to 0
    frappe.db.set_value("Job Card", doc.name, "process_loss_qty", 0.0)

    return stock_name


def update_operation_completed_qty(doc, method):
    """Sync Work Order Operation completed_qty with cumulative produced qty after Job Card submit."""
    if doc.work_order and doc.operation_id:
        produced_qty = frappe.db.get_value("Work Order", doc.work_order, "produced_qty")
        frappe.db.set_value("Work Order Operation", doc.operation_id, "completed_qty", produced_qty)
