import json
import frappe
from frappe.utils import cstr, flt


@frappe.whitelist()
def get_batch_warehouse_details(batch_no, job_card=None, item_code=None, work_order=None):
	"""Compare Job Card (and Work Order) with Batch Number to determine
	the appropriate source warehouse (where batch stock is available)
	and target warehouse (Job Card WIP warehouse).
	"""
	if not batch_no:
		return {}

	# 1. Fetch available stock warehouses for this batch
	batch_warehouses = frappe.db.sql(
		"""
		SELECT sle.warehouse, SUM(sle.actual_qty) as qty
		FROM `tabStock Ledger Entry` sle
		WHERE sle.batch_no = %s AND sle.is_cancelled = 0
		GROUP BY sle.warehouse
		HAVING SUM(sle.actual_qty) > 0
		ORDER BY qty DESC
	""",
		(batch_no,),
		as_dict=True,
	)

	s_warehouse = None
	t_warehouse = None
	available_qty = 0

	# 2. Get Job Card details if linked
	jc_doc = None
	if job_card:
		jc_doc = frappe.db.get_value(
			"Job Card",
			job_card,
			["wip_warehouse", "work_order", "operation"],
			as_dict=True,
		)

	# Target warehouse defaults to Job Card wip_warehouse or Work Order wip_warehouse
	if jc_doc and jc_doc.get("wip_warehouse"):
		t_warehouse = jc_doc.wip_warehouse
	elif work_order:
		t_warehouse = frappe.db.get_value("Work Order", work_order, "wip_warehouse")

	# Check if Job Card Item defines a source_warehouse for this item
	jc_source_warehouse = None
	if job_card and item_code:
		jc_source_warehouse = frappe.db.get_value(
			"Job Card Item",
			{"parent": job_card, "item_code": item_code},
			"source_warehouse",
		)

	# 3. Compare Batch available warehouses with Job Card source warehouse
	if batch_warehouses:
		# Check if batch is present in Job Card's expected source_warehouse
		matching_wh = None
		if jc_source_warehouse:
			for bw in batch_warehouses:
				if bw.warehouse == jc_source_warehouse:
					matching_wh = bw
					break

		if matching_wh:
			s_warehouse = matching_wh.warehouse
			available_qty = matching_wh.qty
		else:
			# If not in Job Card source warehouse, pick warehouse with highest batch qty
			s_warehouse = batch_warehouses[0].warehouse
			available_qty = batch_warehouses[0].qty
	elif jc_source_warehouse:
		s_warehouse = jc_source_warehouse

	return {
		"s_warehouse": s_warehouse,
		"t_warehouse": t_warehouse,
		"available_qty": flt(available_qty),
		"all_warehouses": [bw.warehouse for bw in batch_warehouses],
	}


def sync_stock_entry_batch_numbers(doc, method=None):
	"""Server-side hook: Ensures batch_number and batch_no are synced
	when creating/validating Stock Entry, especially for Material Transfer
	of Stranding or from Job Card.
	"""
	if not doc.get("items"):
		return

	is_stranding = False
	if doc.get("job_card"):
		op = frappe.db.get_value("Job Card", doc.job_card, "operation")
		if op and "strand" in cstr(op).lower():
			is_stranding = True

	for row in doc.items:
		if is_stranding or doc.purpose == "Material Transfer for Manufacture":
			# Sync batch_no -> batch_number
			if row.batch_no and not row.get("batch_number"):
				row.batch_number = row.batch_no
			# Sync batch_number -> batch_no
			elif row.get("batch_number") and not row.batch_no:
				row.batch_no = row.batch_number

			if row.batch_no or row.get("batch_number"):
				row.use_serial_batch_fields = 1

		# Auto-populate custom_batch_qty with full quantity of the batch
		batch = row.get("batch_number") or row.batch_no
		if not batch and row.serial_and_batch_bundle:
			batch = frappe.db.get_value(
				"Serial and Batch Entry",
				{"parent": row.serial_and_batch_bundle},
				"batch_no"
			)
		if batch:
			full_qty = frappe.db.get_value("Batch", batch, "batch_qty")
			if full_qty is not None:
				row.custom_batch_qty = flt(full_qty)


@frappe.whitelist()
def get_incoming_rate(args, raise_error_if_no_rate=True):
	"""Safe wrapper for erpnext.stock.utils.get_incoming_rate to prevent
	ZeroDivisionError when batch_no is provided with qty=0 or warehouse=''.
	"""
	data = None
	if isinstance(args, str):
		try:
			data = json.loads(args)
		except Exception:
			pass
	elif isinstance(args, dict):
		data = dict(args)

	if isinstance(data, dict):
		# If qty is 0, use 1 for valuation calculation
		if flt(data.get("qty")) == 0:
			data["qty"] = 1

		# If warehouse is empty, attempt to resolve from batch's stock ledger entry
		if not data.get("warehouse") and data.get("batch_no"):
			wh = frappe.db.get_value(
				"Stock Ledger Entry",
				{"batch_no": data.get("batch_no"), "is_cancelled": 0},
				"warehouse",
			)
			if wh:
				data["warehouse"] = wh

		if isinstance(args, str):
			args = json.dumps(data)
		elif isinstance(args, dict):
			args = data

	try:
		from erpnext.stock.utils import get_incoming_rate as core_get_incoming_rate

		return core_get_incoming_rate(args, raise_error_if_no_rate)
	except ZeroDivisionError:
		return 0.0
	except Exception as e:
		if "ZeroDivisionError" in str(e) or "division by zero" in str(e):
			return 0.0
		raise


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_batch_no_query(doctype, txt, searchfield, start, page_len, filters):
	"""Custom query for Batch Number search in Stock Entry.
	Supports filtering with or without item_code, avoiding Unknown column 'tabBatch.warehouse'.
	"""
	if isinstance(filters, str):
		try:
			filters = json.loads(filters)
		except Exception:
			filters = {}
	filters = filters or {}

	# If item_code is present, delegate to standard get_batch_no
	if filters.get("item_code"):
		from erpnext.controllers.queries import get_batch_no as core_get_batch_no
		return core_get_batch_no(doctype, txt, searchfield, start, page_len, filters)

	warehouse = filters.get("warehouse")
	conditions = ["b.disabled = 0"]
	params = {}

	if txt:
		conditions.append("(b.name LIKE %(txt)s OR b.item LIKE %(txt)s)")
		params["txt"] = f"%{txt}%"

	start = int(start or 0)
	page_len = int(page_len or 20)
	params["start"] = start
	params["page_len"] = page_len

	if warehouse:
		params["warehouse"] = warehouse
		cond_str = " AND ".join(conditions)
		query = f"""
			SELECT DISTINCT b.name, b.item, SUM(sle.actual_qty) as qty
			FROM `tabBatch` b
			INNER JOIN `tabStock Ledger Entry` sle ON sle.batch_no = b.name
			WHERE sle.warehouse = %(warehouse)s
			  AND sle.is_cancelled = 0
			  AND {cond_str}
			GROUP BY b.name, b.item
			HAVING SUM(sle.actual_qty) > 0
			ORDER BY b.creation DESC
			LIMIT %(start)s, %(page_len)s
		"""
		return frappe.db.sql(query, params, as_list=1)
	else:
		cond_str = " AND ".join(conditions)
		query = f"""
			SELECT b.name, b.item, b.batch_qty
			FROM `tabBatch` b
			WHERE {cond_str}
			ORDER BY b.creation DESC
			LIMIT %(start)s, %(page_len)s
		"""
		return frappe.db.sql(query, params, as_list=1)
