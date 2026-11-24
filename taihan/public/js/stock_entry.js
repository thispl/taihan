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
		row.batch_no = "";
		row.batch_number = "";
		row.custom_batch_qty = 0;
		frm.refresh_field("items");
		return;
	}

	frappe.db
		.get_value("Batch", batch_val, ["item", "batch_qty", "expiry_date", "stock_uom"])
		.then((r) => {
			if (!r || !r.message) return;
			let batch_info = r.message;
			let batch_item = batch_info.item;
			if (!batch_item) return;

			// If row has an item_code already and it differs from the batch's item:
			// Never overwrite an existing item_code with the batch's item!
			if (row.item_code && batch_item && row.item_code !== batch_item) {
				frappe.msgprint(__("Batch {0} belongs to item {1}, not {2}.", [batch_val, batch_item, row.item_code]));
				row[entered_field] = "";
				row.batch_no = "";
				row.batch_number = "";
				frm.refresh_field("items");
				return;
			}

			row.batch_no = batch_val;
			row.batch_number = batch_val;
			row.use_serial_batch_fields = 1;

			if (batch_info.batch_qty !== undefined) {
				row.custom_batch_qty = flt(batch_info.batch_qty);
			}

			// If qty is not yet set, set to batch_qty or default 1
			if (flt(row.qty) <= 0) {
				row.qty = flt(batch_info.batch_qty) || 1;
			}

			// If item_code is not set, set it from the batch
			if (!row.item_code) {
				frappe.flags.hide_serial_batch_dialog = true;
				frappe.model.set_value(cdt, cdn, "item_code", batch_item).then(() => {
					row.use_serial_batch_fields = 1;
					row.batch_no = batch_val;
					row.batch_number = batch_val;
					frappe.flags.hide_serial_batch_dialog = false;
					frm.refresh_field("items");
				});
				return;
			}

			// Compare Job Card and Batch Number to get warehouse details
			let jc_name = frm.doc.job_card || frm.doc.custom_job_card;
			frappe.call({
				method: "taihan.taihan.stock_entry.get_batch_warehouse_details",
				args: {
					batch_no: batch_val,
					job_card: jc_name,
					item_code: row.item_code,
					work_order: frm.doc.work_order,
				},
				callback: function (wh_res) {
					if (wh_res && wh_res.message) {
						let wh_data = wh_res.message;
						if (wh_data.s_warehouse && !row.s_warehouse) {
							row.s_warehouse = wh_data.s_warehouse;
						}
						if (wh_data.t_warehouse && !row.t_warehouse) {
							row.t_warehouse = wh_data.t_warehouse;
						}
					}

					let calc_qty = flt(row.qty) || flt(row.transfer_qty) || 1;
					frappe.flags.hide_serial_batch_dialog = true;
					frappe.call({
						doc: frm.doc,
						method: "get_item_details",
						args: {
							item_code: row.item_code,
							warehouse: cstr(row.s_warehouse) || cstr(row.t_warehouse),
							transfer_qty: row.transfer_qty || calc_qty,
							serial_no: row.serial_no,
							batch_no: batch_val,
							bom_no: row.bom_no,
							expense_account: row.expense_account,
							cost_center: row.cost_center,
							company: frm.doc.company,
							qty: calc_qty,
							voucher_type: frm.doc.doctype,
							voucher_no: row.name,
							allow_zero_valuation: 1,
						},
						callback: function (res) {
							if (res && res.message) {
								$.each(res.message, function (k, v) {
									if (v !== undefined && v !== null && k !== "batch_no" && k !== "batch_number" && k !== "item_code") {
										row[k] = v;
									}
								});
							}
							row.use_serial_batch_fields = 1;
							row.batch_no = batch_val;
							row.batch_number = batch_val;
							frappe.flags.hide_serial_batch_dialog = false;
							frm.refresh_field("items");
						},
						error: function () {
							frappe.flags.hide_serial_batch_dialog = false;
							frm.refresh_field("items");
						}
					});
				},
			});
		});
}

function sync_stranding_job_card_batches(frm) {
	if (!frm.doc.items || !frm.doc.items.length) return;

	// 1. Sync batch_no <-> batch_number and serial_and_batch_bundle for existing values
	let changed = false;
	frm.doc.items.forEach((row) => {
		if (row.batch_no && row.batch_number !== row.batch_no) {
			row.batch_number = row.batch_no;
			row.use_serial_batch_fields = 1;
			changed = true;
		} else if (row.batch_number && row.batch_no !== row.batch_number) {
			row.batch_no = row.batch_number;
			row.use_serial_batch_fields = 1;
			changed = true;
		}

		if (row.serial_and_batch_bundle && (!row.batch_no || !row.batch_number)) {
			frappe.db
				.get_value("Serial and Batch Entry", { parent: row.serial_and_batch_bundle }, "batch_no")
				.then((sbe) => {
					if (sbe && sbe.message && sbe.message.batch_no) {
						let b = sbe.message.batch_no;
						row.batch_no = b;
						row.batch_number = b;
						row.use_serial_batch_fields = 1;
						frm.refresh_field("items");
					}
				});
		}

		if (row.batch_number || row.batch_no) {
			row.use_serial_batch_fields = 1;
		}
	});

	if (changed) {
		frm.refresh_field("items");
	}

	// NOTE: Do NOT pre-fill the Job Card's previous batch on Manufacture
	// finished rows - an empty batch lets ERPNext auto-create a NEW Batch on
	// submit. Copying the old batch would merge this run's output into the
	// earlier partial-production batch.
}

function sync_all_batch_quantities(frm) {
	if (!frm.doc.items || !frm.doc.items.length) return;

	// Assign row.custom_batch_qty directly (not via frappe.model.set_value) so
	// this display-only sync does not mark the form dirty after save. Only a
	// positive batch_qty is synced - a null/0 value would otherwise wipe the
	// saved quantity on every refresh.
	let changed = false;
	let tasks = [];

	frm.doc.items.forEach((row) => {
		let batch = row.batch_number || row.batch_no;
		if (batch) {
			tasks.push(
				frappe.db.get_value("Batch", batch, "batch_qty").then((r) => {
					let bq = r && r.message ? flt(r.message.batch_qty) : 0;
					if (bq > 0 && flt(row.custom_batch_qty) !== bq) {
						row.custom_batch_qty = bq;
						changed = true;
					}
				})
			);
		} else if (row.serial_and_batch_bundle) {
			tasks.push(
				frappe.db
					.get_value("Serial and Batch Entry", { parent: row.serial_and_batch_bundle }, "batch_no")
					.then((sbe) => {
						if (sbe && sbe.message && sbe.message.batch_no) {
							return frappe.db
								.get_value("Batch", sbe.message.batch_no, "batch_qty")
								.then((r) => {
									let bq = r && r.message ? flt(r.message.batch_qty) : 0;
									if (bq > 0 && flt(row.custom_batch_qty) !== bq) {
										row.custom_batch_qty = bq;
										changed = true;
									}
								});
						}
					})
			);
		}
	});

	Promise.all(tasks).then(() => {
		if (changed) frm.refresh_field("items");
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

	custom_job_card: function (frm) {
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
							let bq = r && r.message ? flt(r.message.batch_qty) : 0;
							if (bq > 0) {
								frappe.model.set_value(cdt, cdn, "custom_batch_qty", bq);
							}
						});
					}
				});
		}
	},
});
