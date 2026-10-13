frappe.provide("taihan.stock_entry");

function setup_stock_entry_grid_batch_no(frm) {
	if (!frm.fields_dict.items || !frm.fields_dict.items.grid) return;
	let grid = frm.fields_dict.items.grid;

	// 1. Set explicit column sizes so visible columns fit within Frappe's 11-column limit
	const col_widths = {
		s_warehouse: 1,
		t_warehouse: 1,
		item_code: 2,
		batch_number: 2,
		qty: 1,
		custom_batch_qty: 1,
		basic_rate: 1,
		custom_employee: 1,
		custom_department: 1,
	};

	Object.keys(col_widths).forEach((fname) => {
		let w = col_widths[fname];
		let df = frappe.meta.get_docfield("Stock Entry Detail", fname, frm.docname);
		if (df) {
			df.in_list_view = 1;
			df.columns = w;
		}
		let grid_df = grid.docfields ? grid.docfields.find((d) => d.fieldname === fname) : null;
		if (grid_df) {
			grid_df.in_list_view = 1;
			grid_df.columns = w;
		}
	});

	// Keep batch_no out of duplicate column in list view
	let bno_df = frappe.meta.get_docfield("Stock Entry Detail", "batch_no", frm.docname);
	if (bno_df) {
		bno_df.in_list_view = 0;
		bno_df.depends_on = "";
	}
	let grid_bno_df = grid.docfields ? grid.docfields.find((d) => d.fieldname === "batch_no") : null;
	if (grid_bno_df) {
		grid_bno_df.in_list_view = 0;
		grid_bno_df.depends_on = "";
	}

	// Clear any cached user-defined column customizations so layout is uniform for all users
	grid.user_defined_columns = [];
	let user_settings = frappe.get_user_settings ? frappe.get_user_settings(frm.doctype, "GridView") : null;
	if (user_settings && user_settings["Stock Entry Detail"]) {
		delete user_settings["Stock Entry Detail"];
	}

	grid.visible_columns = null;
	grid.setup_visible_columns();

	if (grid.visible_columns) {
		// Filter out duplicate batch_no column
		grid.visible_columns = grid.visible_columns.filter((c) => c[0] && c[0].fieldname !== "batch_no");

		// 1. Ensure batch_number is ALWAYS present and positioned right after item_code
		let bn_field = grid.docfields ? grid.docfields.find((d) => d.fieldname === "batch_number") : null;
		let bn_idx = grid.visible_columns.findIndex((c) => c[0] && c[0].fieldname === "batch_number");
		let item_idx = grid.visible_columns.findIndex((c) => c[0] && c[0].fieldname === "item_code");

		if (bn_idx === -1 && bn_field) {
			if (item_idx !== -1) {
				grid.visible_columns.splice(item_idx + 1, 0, [bn_field, 2]);
			} else {
				grid.visible_columns.push([bn_field, 2]);
			}
		} else if (bn_idx !== -1 && item_idx !== -1 && bn_idx !== item_idx + 1) {
			let bn_col = grid.visible_columns.splice(bn_idx, 1)[0];
			let new_item_idx = grid.visible_columns.findIndex((c) => c[0] && c[0].fieldname === "item_code");
			grid.visible_columns.splice(new_item_idx + 1, 0, bn_col);
		}

		// 2. Ensure custom_batch_qty is ALWAYS present and positioned right after qty
		let bq_field = grid.docfields ? grid.docfields.find((d) => d.fieldname === "custom_batch_qty") : null;
		let bq_idx = grid.visible_columns.findIndex((c) => c[0] && c[0].fieldname === "custom_batch_qty");
		let qty_idx = grid.visible_columns.findIndex((c) => c[0] && c[0].fieldname === "qty");

		if (bq_idx === -1 && bq_field) {
			if (qty_idx !== -1) {
				grid.visible_columns.splice(qty_idx + 1, 0, [bq_field, 1]);
			} else {
				grid.visible_columns.push([bq_field, 1]);
			}
		} else if (bq_idx !== -1 && qty_idx !== -1 && bq_idx !== qty_idx + 1) {
			let bq_col = grid.visible_columns.splice(bq_idx, 1)[0];
			let new_qty_idx = grid.visible_columns.findIndex((c) => c[0] && c[0].fieldname === "qty");
			grid.visible_columns.splice(new_qty_idx + 1, 0, bq_col);
		}
	}
	grid.reset_grid();
}

function setup_batch_field_queries(frm) {
	const batch_query_fn = function (doc, cdt, cdn) {
		let item = locals[cdt][cdn];
		let filters = {};

		if (item && item.item_code) {
			if (
				in_list(
					[
						"Material Transfer for Manufacture",
						"Manufacture",
						"Repack",
						"Send to Subcontractor",
					],
					doc.purpose
				)
			) {
				filters = {
					item_code: item.item_code,
					posting_date: frm.doc.posting_date || frappe.datetime.nowdate(),
				};
			} else {
				filters = {
					item_code: item.item_code,
				};
			}

			if (frm.doc.purpose !== "Material Receipt") {
				filters["warehouse"] = item.s_warehouse || item.t_warehouse;
			}

			if (!item.s_warehouse && item.t_warehouse) {
				filters["is_inward"] = 1;
			}
		} else {
			filters["disabled"] = 0;
			if (frm.doc.purpose !== "Material Receipt" && (item?.s_warehouse || item?.t_warehouse)) {
				filters["warehouse"] = item.s_warehouse || item.t_warehouse;
			}
		}

		return {
			query: "taihan.taihan.stock_entry.get_batch_no_query",
			filters: filters,
		};
	};

	frm.set_query("batch_number", "items", batch_query_fn);
	frm.set_query("batch_no", "items", batch_query_fn);
}

function hook_safe_set_basic_rate(frm) {
	if (frm.events.set_basic_rate && !frm.events.set_basic_rate.__safe_wrapped) {
		let orig_set_basic_rate = frm.events.set_basic_rate;
		let safe_set_basic_rate = function (frm, cdt, cdn) {
			let item = locals[cdt][cdn];
			if (item && (flt(item.qty) <= 0 || (!item.s_warehouse && !item.t_warehouse))) {
				frappe.model.set_value(cdt, cdn, "basic_rate", 0.0);
				if (frm.events.calculate_basic_amount) {
					frm.events.calculate_basic_amount(frm, item);
				}
				return;
			}
			orig_set_basic_rate(frm, cdt, cdn);
		};
		safe_set_basic_rate.__safe_wrapped = true;
		frm.events.set_basic_rate = safe_set_basic_rate;
	}
}

function handle_batch_entry(frm, cdt, cdn, entered_field) {
	let row = locals[cdt][cdn];
	if (!row) return;

	let batch_val = row[entered_field];
	if (!batch_val) {
		frappe.model.set_value(cdt, cdn, "custom_batch_qty", 0);
		return;
	}

	row.batch_no = batch_val;
	row.batch_number = batch_val;
	row.use_serial_batch_fields = 1;

	frappe.db
		.get_value("Batch", batch_val, ["item", "batch_qty", "expiry_date", "stock_uom"])
		.then((r) => {
			if (!r || !r.message) return;
			let batch_info = r.message;
			let batch_item = batch_info.item;
			if (!batch_item) return;

			if (batch_info.batch_qty !== undefined) {
				frappe.model.set_value(cdt, cdn, "custom_batch_qty", flt(batch_info.batch_qty));
			}

			// If qty is not yet set, set to batch_qty or default 1
			if (flt(row.qty) <= 0) {
				row.qty = flt(batch_info.batch_qty) || 1;
				frappe.model.set_value(cdt, cdn, "qty", row.qty);
			}

			// Compare Job Card and Batch Number to get warehouse details
			frappe.call({
				method: "taihan.taihan.stock_entry.get_batch_warehouse_details",
				args: {
					batch_no: batch_val,
					job_card: frm.doc.job_card,
					item_code: batch_item,
					work_order: frm.doc.work_order,
				},
				callback: function (wh_res) {
					if (wh_res && wh_res.message) {
						let wh_data = wh_res.message;
						if (wh_data.s_warehouse && !row.s_warehouse) {
							frappe.model.set_value(cdt, cdn, "s_warehouse", wh_data.s_warehouse);
						}
						if (wh_data.t_warehouse && !row.t_warehouse) {
							frappe.model.set_value(cdt, cdn, "t_warehouse", wh_data.t_warehouse);
						}
					}

					frappe.model.set_value(cdt, cdn, "use_serial_batch_fields", 1);
					frappe.model.set_value(cdt, cdn, "batch_no", batch_val);
					frappe.model.set_value(cdt, cdn, "batch_number", batch_val);

					// Fetch Item Code and details if different or empty
					if (row.item_code !== batch_item) {
						frappe.flags.hide_serial_batch_dialog = true;
						frappe.model.set_value(cdt, cdn, "item_code", batch_item).then(() => {
							frappe.model.set_value(cdt, cdn, "use_serial_batch_fields", 1);
							frappe.model.set_value(cdt, cdn, "batch_no", batch_val);
							frappe.model.set_value(cdt, cdn, "batch_number", batch_val);
							frappe.flags.hide_serial_batch_dialog = false;
							frm.refresh_field("items");
						});
					} else {
						// Item code is already set, call get_item_details to fetch rate, account, etc.
						frappe.flags.hide_serial_batch_dialog = true;
						frappe.call({
							doc: frm.doc,
							method: "get_item_details",
							args: {
								item_code: row.item_code,
								warehouse: cstr(row.s_warehouse) || cstr(row.t_warehouse),
								transfer_qty: row.transfer_qty,
								serial_no: row.serial_no,
								batch_no: batch_val,
								bom_no: row.bom_no,
								expense_account: row.expense_account,
								cost_center: row.cost_center,
								company: frm.doc.company,
								qty: row.qty,
								voucher_type: frm.doc.doctype,
								voucher_no: row.name,
								allow_zero_valuation: 1,
							},
							callback: function (res) {
								if (res && res.message) {
									$.each(res.message, function (k, v) {
										if (v !== undefined && v !== null && k !== "batch_no" && k !== "batch_number") {
											frappe.model.set_value(cdt, cdn, k, v);
										}
									});
								}
								frappe.model.set_value(cdt, cdn, "use_serial_batch_fields", 1);
								frappe.model.set_value(cdt, cdn, "batch_no", batch_val);
								frappe.model.set_value(cdt, cdn, "batch_number", batch_val);
								frappe.flags.hide_serial_batch_dialog = false;
								frm.refresh_field("items");
							},
						});
					}
				},
			});
		});
}

function sync_stranding_job_card_batches(frm) {
	if (!frm.doc.job_card || !frm.doc.items || !frm.doc.items.length) return;

	frappe.db
		.get_value("Job Card", frm.doc.job_card, ["operation", "batch_no", "wip_warehouse"])
		.then((r) => {
			if (!r || !r.message) return;
			let jc = r.message;
			let op_lower = (jc.operation || "").toLowerCase();
			let is_stranding =
				op_lower.includes("strand") ||
				frm.doc.purpose === "Material Transfer for Manufacture" ||
				frm.doc.stock_entry_type === "Material Transfer for Manufacture";

			if (is_stranding) {
				frm.doc.items.forEach((row) => {
					let changed = false;
					if (row.batch_no && row.batch_number !== row.batch_no) {
						frappe.model.set_value(row.doctype, row.name, "batch_number", row.batch_no);
						changed = true;
					} else if (row.batch_number && row.batch_no !== row.batch_number) {
						frappe.model.set_value(row.doctype, row.name, "batch_no", row.batch_number);
						changed = true;
					} else if (!row.batch_no && !row.batch_number && jc.batch_no) {
						frappe.model.set_value(row.doctype, row.name, "batch_number", jc.batch_no);
						frappe.model.set_value(row.doctype, row.name, "batch_no", jc.batch_no);
						changed = true;
					}

					let current_batch = row.batch_number || row.batch_no;
					if (current_batch) {
						frappe.model.set_value(row.doctype, row.name, "use_serial_batch_fields", 1);
						if (!row.s_warehouse || !row.t_warehouse) {
							frappe.call({
								method: "taihan.taihan.stock_entry.get_batch_warehouse_details",
								args: {
									batch_no: current_batch,
									job_card: frm.doc.job_card,
									item_code: row.item_code,
									work_order: frm.doc.work_order,
								},
								callback: function (wh_res) {
									if (wh_res && wh_res.message) {
										let wh_data = wh_res.message;
										if (wh_data.s_warehouse && !row.s_warehouse) {
											frappe.model.set_value(row.doctype, row.name, "s_warehouse", wh_data.s_warehouse);
										}
										if (wh_data.t_warehouse && !row.t_warehouse) {
											frappe.model.set_value(row.doctype, row.name, "t_warehouse", wh_data.t_warehouse);
										}
										frm.refresh_field("items");
									}
								},
							});
						}
					}
					if (changed) {
						frm.refresh_field("items");
					}
				});
			}
		});
}

function sync_all_batch_quantities(frm) {
	if (!frm.doc.items || !frm.doc.items.length) return;
	frm.doc.items.forEach((row) => {
		let batch = row.batch_number || row.batch_no;
		if (batch) {
			frappe.db.get_value("Batch", batch, "batch_qty").then((r) => {
				if (r && r.message && r.message.batch_qty !== undefined) {
					let bq = flt(r.message.batch_qty);
					if (flt(row.custom_batch_qty) !== bq) {
						frappe.model.set_value(row.doctype, row.name, "custom_batch_qty", bq);
					}
				}
			});
		} else if (row.serial_and_batch_bundle) {
			frappe.db
				.get_value("Serial and Batch Entry", { parent: row.serial_and_batch_bundle }, "batch_no")
				.then((sbe) => {
					if (sbe && sbe.message && sbe.message.batch_no) {
						frappe.db.get_value("Batch", sbe.message.batch_no, "batch_qty").then((r) => {
							if (r && r.message && r.message.batch_qty !== undefined) {
								let bq = flt(r.message.batch_qty);
								if (flt(row.custom_batch_qty) !== bq) {
									frappe.model.set_value(row.doctype, row.name, "custom_batch_qty", bq);
								}
							}
						});
					}
				});
		}
	});
}

frappe.ui.form.on("Stock Entry", {
	setup: function (frm) {
		setup_stock_entry_grid_batch_no(frm);
		setup_batch_field_queries(frm);
		hook_safe_set_basic_rate(frm);
	},

	onload: function (frm) {
		setup_stock_entry_grid_batch_no(frm);
		setup_batch_field_queries(frm);
		hook_safe_set_basic_rate(frm);
		sync_stranding_job_card_batches(frm);
		sync_all_batch_quantities(frm);
	},

	refresh: function (frm) {
		setup_stock_entry_grid_batch_no(frm);
		setup_batch_field_queries(frm);
		hook_safe_set_basic_rate(frm);
		sync_stranding_job_card_batches(frm);
		sync_all_batch_quantities(frm);
	},

	job_card: function (frm) {
		sync_stranding_job_card_batches(frm);
	},

	items_add: function (frm, cdt, cdn) {
		frappe.model.set_value(cdt, cdn, "use_serial_batch_fields", 1);
	},
});

frappe.ui.form.on("Stock Entry Detail", {
	items_add: function (frm, cdt, cdn) {
		frappe.model.set_value(cdt, cdn, "use_serial_batch_fields", 1);
	},

	batch_number: function (frm, cdt, cdn) {
		handle_batch_entry(frm, cdt, cdn, "batch_number");
	},

	batch_no: function (frm, cdt, cdn) {
		handle_batch_entry(frm, cdt, cdn, "batch_no");
	},

	serial_and_batch_bundle: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row && row.serial_and_batch_bundle) {
			frappe.db
				.get_value("Serial and Batch Entry", { parent: row.serial_and_batch_bundle }, "batch_no")
				.then((sbe) => {
					if (sbe && sbe.message && sbe.message.batch_no) {
						frappe.db.get_value("Batch", sbe.message.batch_no, "batch_qty").then((r) => {
							if (r && r.message && r.message.batch_qty !== undefined) {
								frappe.model.set_value(cdt, cdn, "custom_batch_qty", flt(r.message.batch_qty));
							}
						});
					}
				});
		}
	},
});
