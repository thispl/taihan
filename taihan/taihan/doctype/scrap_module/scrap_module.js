// Copyright (c) 2025, Teampro and contributors
// For license information, please see license.txt

frappe.ui.form.on("Scrap Module", {
	item_code(frm) {
		frm.set_query("batch", function () {
			return {
				filters: {
					item: frm.doc.item_code,
					disabled: 0,
				},
			};
		});
	},

	warehouse(frm) {
		if (frm.doc.batch && frm.doc.warehouse) {
			update_batch_qty_for_warehouse(frm);
		}
	},

	batch(frm) {
		if (frm.doc.item_code && frm.doc.batch) {
			fetch_batch_details(frm);
		}
	},
});

function update_batch_qty_for_warehouse(frm) {
	frappe.call({
		method: "erpnext.stock.doctype.batch.batch.get_batch_qty",
		args: {
			batch_no: frm.doc.batch,
			warehouse: frm.doc.warehouse,
		},
		callback: function (res) {
			let balance = flt(res.message);
			frm.set_value("qty", balance);
		},
	});
}

function fetch_batch_details(frm) {
	frappe.db
		.get_value(
			"Batch",
			{ item: frm.doc.item_code, name: frm.doc.batch },
			["batch_qty", "reference_name"]
		)
		.then((r) => {
			if (!r.message) return;

			// If warehouse is already selected, fetch balance for that warehouse
			if (frm.doc.warehouse) {
				update_batch_qty_for_warehouse(frm);
			} else {
				// Get live batch balance across warehouses
				frappe.call({
					method: "erpnext.stock.doctype.batch.batch.get_batch_qty",
					args: {
						batch_no: frm.doc.batch,
						item_code: frm.doc.item_code,
					},
					callback: function (res) {
						let batch_lines = (res.message || []).filter((row) => flt(row.qty) > 0);
						if (batch_lines.length > 0) {
							// Sort descending by qty to pick warehouse with largest available balance
							batch_lines.sort((a, b) => flt(b.qty) - flt(a.qty));
							frm.set_value("qty", flt(batch_lines[0].qty));
							frm.set_value("warehouse", batch_lines[0].warehouse);
						} else {
							frm.set_value("qty", 0);
						}
					},
				});
			}

			// Pull Job Card / Work Order / Sales Order / Customer from Batch Stock Entry
			if (r.message.reference_name) {
				let stock_entry = r.message.reference_name;
				frappe.db
					.get_value(
						"Stock Entry",
						{ name: stock_entry },
						["custom_job_card", "job_card"]
					)
					.then((se) => {
						let job_card = se.message ? se.message.custom_job_card || se.message.job_card : null;
						if (job_card) {
							frappe.db
								.get_value(
									"Job Card",
									{ name: job_card },
									["name", "work_order", "custom_sales_order", "custom_customer_name"]
								)
								.then((jc) => {
									if (jc.message) {
										frm.set_value("job_card", jc.message.name);
										frm.set_value("work_order", jc.message.work_order);
										frm.set_value("sales_order", jc.message.custom_sales_order);
										frm.set_value("customer", jc.message.custom_customer_name);
									}
								});
						}
					});
			}
		});
}
