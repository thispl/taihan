frappe.dom.set_style(`
	[data-doctype="Job Card"] .stopwatch,
	[data-doctype="Job Card"] .inner-page-message:has(.stopwatch) {
		display: none !important;
	}
`);

frappe.ui.form.on("Job Card", {
	make_dashboard: function (frm) {
		frm.dashboard.refresh();
		hide_job_card_timer(frm);
	},
	hide_timer: function (frm) {
		hide_job_card_timer(frm);
	},
	work_order: function (frm) {
		if (frm.doc.work_order) {
			frappe.db.get_value(
				"Work Order",
				frm.doc.work_order,
				["custom_tube_thickness", "custom_tube_color", "custom_loose_tube_color"],
				function (r) {
					if (r) {
						if (r.custom_tube_thickness && !frm.doc.custom_tube_thickness) {
							frm.set_value("custom_tube_thickness", r.custom_tube_thickness);
						}
						if (r.custom_tube_color && !frm.doc.custom_tube_color) {
							frm.set_value("custom_tube_color", r.custom_tube_color);
						}
					}
				}
			);
		}
	},
	refresh: function (frm) {
		hide_job_card_timer(frm);

		setup_process_job_button(frm);

		if (
			frm.doc.docstatus === 0 &&
			!frm.is_new() &&
			flt(frm.doc.total_completed_qty) > 0 &&
			flt(frm.doc.total_completed_qty) < flt(frm.doc.for_quantity)
		) {
			frm.add_custom_button(
				__("Complete Partial Production"),
				function () {
					let completed_qty = flt(frm.doc.total_completed_qty);
					let remaining = flt(frm.doc.for_quantity) - completed_qty;

					frappe.confirm(
						__("Complete {0} units now and continue the same Job Card for the remaining {1} units later?", [
							completed_qty,
							remaining,
						]),
						function () {
							frappe.call({
								method: "taihan.taihan.job_card_partial.create_partial_stock_entry",
								args: {
									job_card: frm.doc.name,
								},
								callback: function (r) {
									if (r.message) {
										frappe.show_alert({
											message: __("Batch created for {0} units. Job Card reset to {1} units for future production.", [
												completed_qty,
												remaining,
											]),
											indicator: "green",
										});
										frm.reload_doc();
									}
								},
							});
						}
					);
				},
				__("Actions")
			);
		}

		// Overproduction approval buttons
		let status = frm.doc.custom_overproduction_status || "";
		let is_approved =
			status === "Approved" ||
			frm.doc.custom_overproduction_approved == 1;

		function remove_overproduction_approval_buttons() {
			frm.remove_custom_button(__("Send for Approval"), __("Overproduction"));
			frm.remove_custom_button(__("Approve"), __("Overproduction"));
			frm.remove_custom_button(__("Reject"), __("Overproduction"));
			frm.remove_custom_button("Send for Approval", "Overproduction");
			frm.remove_custom_button("Approve", "Overproduction");
			frm.remove_custom_button("Reject", "Overproduction");
			frm.remove_custom_button(__("Send for Approval"));
			frm.remove_custom_button(__("Approve"));
			frm.remove_custom_button(__("Reject"));
			frm.remove_custom_button("Send for Approval");
			frm.remove_custom_button("Approve");
			frm.remove_custom_button("Reject");
			frm.remove_custom_button(__("Approval"));
			frm.remove_custom_button("Approval");

			if (frm.page && frm.page.wrapper) {
				frm.page.wrapper.find(".inner-group-button, .dropdown-menu").find("a, button, li").filter(function () {
					let txt = ($(this).text() || "").trim();
					return [
						"Approve",
						__("Approve"),
						"Reject",
						__("Reject"),
						"Send for Approval",
						__("Send for Approval"),
						"Approval",
						__("Approval"),
					].includes(txt);
				}).remove();
			}
		}

		if (is_approved || frm.doc.docstatus !== 0 || flt(frm.doc.custom_excess_qty) <= 0) {
			remove_overproduction_approval_buttons();
			setTimeout(remove_overproduction_approval_buttons, 100);
			setTimeout(remove_overproduction_approval_buttons, 300);
		}

		if (
			frm.doc.docstatus === 0 &&
			!frm.is_new() &&
			flt(frm.doc.custom_excess_qty) > 0
		) {
			let is_approver =
				frappe.user.has_role("Overproduction Approver") ||
				frappe.session.user === "arif@taihankw.com" ||
				frappe.session.user === "Administrator";

			if (!is_approved && (!status || status === "Rejected")) {
				frm.add_custom_button(
					__("Send for Approval"),
					function () {
						frappe.call({
							method: "taihan.taihan.job_card.request_overproduction_approval",
							args: {
								job_card: frm.doc.name,
							},
							callback: function (r) {
								frappe.show_alert({
									message: __(r.message.message),
									indicator: "green",
								});
								frm.reload_doc();
							},
						});
					},
					__("Overproduction")
				);
			}

			if (!is_approved && status === "Pending" && is_approver) {
				frm.add_custom_button(
					__("Approve"),
					function () {
						frappe.prompt(
							[
								{
									fieldname: "remarks",
									fieldtype: "Small Text",
									label: __("Remarks (optional)"),
								},
							],
							function (values) {
								frappe.call({
									method: "taihan.taihan.job_card.approve_overproduction",
									args: {
										job_card: frm.doc.name,
										remarks: values.remarks || "",
									},
									callback: function () {
										remove_overproduction_approval_buttons();
										frappe.show_alert({
											message: __("Approved"),
											indicator: "green",
										});
										frm.reload_doc();
									},
								});
							},
							__("Approve Overproduction"),
							__("Approve")
						);
					},
					__("Overproduction")
				);

				frm.add_custom_button(
					__("Reject"),
					function () {
						frappe.prompt(
							[
								{
									fieldname: "remarks",
									fieldtype: "Small Text",
									label: __("Rejection Reason"),
									reqd: 1,
								},
							],
							function (values) {
								frappe.call({
									method: "taihan.taihan.job_card.reject_overproduction",
									args: {
										job_card: frm.doc.name,
										remarks: values.remarks,
									},
									callback: function () {
										remove_overproduction_approval_buttons();
										frappe.show_alert({
											message: __("Rejected"),
											indicator: "red",
										});
										frm.reload_doc();
									},
								});
							},
							__("Reject Overproduction"),
							__("Reject")
						);
					},
					__("Overproduction")
				);
			}

			if (is_approved) {
				remove_overproduction_approval_buttons();
				setTimeout(remove_overproduction_approval_buttons, 100);
				setTimeout(remove_overproduction_approval_buttons, 300);

				frappe.db.get_value(
					"Stock Entry",
					{
						custom_work_order: frm.doc.work_order,
						custom_is_excess_entry: 1,
						docstatus: 1,
					},
					"name",
					(r) => {
						if (r && r.name) {
							frm.add_custom_button(
								__("View Excess Material Transfer"),
								function () {
									frappe.set_route("Form", "Stock Entry", r.name);
								},
								__("Overproduction")
							);
						} else {
							frm.add_custom_button(
								__("Create Excess Material Transfer"),
								function () {
									frappe.call({
										method: "taihan.taihan.job_card.create_excess_stock_entry",
										args: {
											job_card: frm.doc.name,
										},
										freeze: true,
										freeze_message: __("Creating Excess Material Transfer..."),
										callback: function (res) {
											if (res.message && res.message.name) {
												frappe.show_alert({
													message: __("Created Stock Entry {0}", [res.message.name]),
													indicator: "green",
												});
												frm.reload_doc();
											}
										},
									});
								},
								__("Overproduction")
							);
						}
					}
				);
			}
		}
	},
});

function hide_job_card_timer(frm) {
	if (frm.toolbar && frm.toolbar.page && frm.toolbar.page.inner_toolbar) {
		frm.toolbar.page.inner_toolbar.find(".stopwatch").closest(".inner-page-message").remove();
		frm.toolbar.page.inner_toolbar.find(".stopwatch").remove();
	}
	if (frm.page && frm.page.wrapper) {
		frm.page.wrapper.find(".stopwatch").closest(".inner-page-message").remove();
		frm.page.wrapper.find(".stopwatch").remove();
	}
}

function setup_process_job_button(frm) {
	function hide_obsolete_buttons() {
		hide_job_card_timer(frm);
		frm.remove_custom_button(__("Start Job"));
		frm.remove_custom_button(__("Complete Job"));
		frm.remove_custom_button(__("Pause Job"));
		frm.remove_custom_button(__("Resume Job"));
		frm.remove_custom_button("Start Job");
		frm.remove_custom_button("Complete Job");
		frm.remove_custom_button("Pause Job");
		frm.remove_custom_button("Resume Job");

		if (frm.page && frm.page.wrapper) {
			frm.page.wrapper.find(".btn, button").filter(function () {
				let txt = ($(this).text() || "").trim();
				return [
					__("Start Job"),
					"Start Job",
					__("Complete Job"),
					"Complete Job",
					__("Pause Job"),
					"Pause Job",
					__("Resume Job"),
					"Resume Job",
				].includes(txt);
			}).hide();
		}
	}

	hide_obsolete_buttons();
	setTimeout(hide_obsolete_buttons, 100);
	setTimeout(hide_obsolete_buttons, 300);
	setTimeout(hide_obsolete_buttons, 600);

	if (
		frm.doc.docstatus === 0 &&
		!frm.is_new() &&
		(flt(frm.doc.for_quantity) > flt(frm.doc.total_completed_qty) || !frm.doc.for_quantity) &&
		(frm.doc.items || !frm.doc.items.length || flt(frm.doc.for_quantity) === flt(frm.doc.transferred_qty))
	) {
		if (frm.doc.work_order) {
			frappe.db.get_value(
				"Work Order",
				frm.doc.work_order,
				["skip_transfer", "status"],
				(result) => {
					if (
						result &&
						(result.skip_transfer === 1 ||
							result.status === "In Process" ||
							flt(frm.doc.transferred_qty) > 0 ||
							!frm.doc.items.length)
					) {
						add_process_job_button(frm);
					}
				}
			);
		} else {
			add_process_job_button(frm);
		}
	}
}

function add_process_job_button(frm) {
	if (!frm.page || !frm.page.wrapper) return;

	let exists = false;
	frm.page.wrapper.find(".btn, button").each(function () {
		let txt = ($(this).text() || "").trim();
		if (txt === __("Process Job") || txt === "Process Job") {
			exists = true;
		}
	});

	if (!exists) {
		frm.add_custom_button(__("Process Job"), function () {
			open_complete_job_dialog(frm);
		}).addClass("btn-primary");
	}
}

function open_complete_job_dialog(frm) {
	let remaining_qty = flt(frm.doc.for_quantity) - flt(frm.doc.total_completed_qty);
	if (remaining_qty < 0) remaining_qty = 0;

	let default_cycle_qty = remaining_qty > 0 ? remaining_qty : flt(frm.doc.for_quantity);
	let timezone =
		(frappe.boot.time_zone && (frappe.boot.time_zone.user || frappe.boot.time_zone.system)) ||
		"Asia/Kolkata";

	let default_employee = "";
	if (frm.doc.employee && frm.doc.employee.length) {
		default_employee = frm.doc.employee[0].employee || "";
	}
	if (!default_employee && frm.doc.time_logs && frm.doc.time_logs.length) {
		default_employee = frm.doc.time_logs[frm.doc.time_logs.length - 1].employee || "";
	}

	function set_field_value(dialog_obj, fieldname, val) {
		let f = dialog_obj.fields_dict[fieldname];
		if (f) {
			let num = flt(val);
			f.value = num;
			f.set_input(num);
		}
	}

	let dialog = new frappe.ui.Dialog({
		title: __("Complete Job"),
		fields: [
			{
				fieldname: "employee",
				label: __("Employee"),
				fieldtype: "Link",
				options: "Employee",
				reqd: 1,
				default: default_employee,
			},
			{
				fieldname: "qty_to_manufacture",
				label: __("Qty to Manufacture in this Cycle"),
				fieldtype: "Float",
				reqd: 1,
				default: default_cycle_qty,
				description: __("Target qty for this cycle. If Completed Qty exceeds this, excess will follow Overproduction Approval."),
				onchange: function () {
					let m = flt(dialog.get_value("qty_to_manufacture"));
					let c = flt(dialog.get_value("completed_qty"));
					let l = flt(dialog.get_value("process_loss_qty"));

					let p = Math.max(0, m - c - l);
					set_field_value(dialog, "pending_qty", p);
				},
			},
			{
				fieldname: "completed_qty",
				label: __("Completed Quantity"),
				fieldtype: "Float",
				reqd: 1,
				default: default_cycle_qty,
				onchange: function () {
					let m = flt(dialog.get_value("qty_to_manufacture"));
					let c = flt(dialog.get_value("completed_qty"));
					let l = flt(dialog.get_value("process_loss_qty"));

					let p = Math.max(0, m - c - l);
					set_field_value(dialog, "pending_qty", p);
				},
			},
			{
				fieldname: "pending_qty",
				label: __("Pending Quantity"),
				fieldtype: "Float",
				default: 0.0,
				description: __("Qty left for a later cycle or for another job card."),
				onchange: function () {
					let m = flt(dialog.get_value("qty_to_manufacture"));
					let c = flt(dialog.get_value("completed_qty"));
					let l = flt(dialog.get_value("process_loss_qty"));
					let expected_p = Math.max(0, m - c - l);
					let entered_p = flt(dialog.get_value("pending_qty"));

					if (Math.abs(entered_p - expected_p) > 0.001) {
						if (c + l >= m) {
							frappe.msgprint(
								__(
									"Completed Quantity is {0} and Process Loss is {1}. Pending Quantity cannot be modified (must be 0).",
									[c, l]
								)
							);
						} else {
							frappe.msgprint(
								__(
									"Pending Quantity is automatically calculated as Qty to Manufacture ({0}) - Completed Quantity ({1}) - Process Loss ({2}) = {3}. Please change Completed Quantity or Process Loss Quantity instead.",
									[m, c, l, expected_p]
								)
							);
						}
						set_field_value(dialog, "pending_qty", expected_p);
					}
				},
			},
			{
				fieldname: "process_loss_qty",
				label: __("Process Loss Quantity"),
				fieldtype: "Float",
				default: 0.0,
				description: __("Qty scrapped in this cycle, nobody will produce it."),
				onchange: function () {
					let m = flt(dialog.get_value("qty_to_manufacture"));
					let c = flt(dialog.get_value("completed_qty"));
					let l = flt(dialog.get_value("process_loss_qty"));

					let p = Math.max(0, m - c - l);
					set_field_value(dialog, "pending_qty", p);
				},
			},
			{
				fieldname: "sec_break",
				fieldtype: "Section Break",
			},
			{
				fieldname: "end_time",
				label: __("End Time"),
				fieldtype: "Datetime",
				default: frappe.datetime.now_datetime(),
				description: timezone,
			},
		],
		primary_action_label: __("Update"),
		primary_action: function (values) {
			if (!values.employee) {
				frappe.msgprint(__("Please select an Employee."));
				return;
			}

			let m = flt(values.qty_to_manufacture);
			let c = flt(values.completed_qty);
			let p = flt(values.pending_qty);
			let l = flt(values.process_loss_qty);

			if (c <= 0 && m > 0 && p === 0 && l === 0) {
				frappe.msgprint(__("Completed Quantity must be greater than 0."));
				return;
			}

			// If completed + process loss is less than target, validate pending
			if (c + l < m) {
				let expected_p = m - c - l;
				if (Math.abs(p - expected_p) > 0.001) {
					frappe.msgprint(
						__(
							"Completed ({0}), Pending ({1}) and Process Loss ({2}) quantities must add up to Qty to Manufacture ({3}). Current sum is {4}.",
							[c, p, l, m, c + p + l]
						)
					);
					return;
				}
			} else {
				// Target met or overproduction: pending qty must be 0
				p = 0;
			}

			// Validate End Time vs Start Time
			let start_time = (frm.doc.time_logs && frm.doc.time_logs.length)
				? frm.doc.time_logs[frm.doc.time_logs.length - 1].to_time
				: frm.doc.creation;
			if (start_time && values.end_time) {
				if (moment(values.end_time).isSameOrBefore(moment(start_time))) {
					frappe.msgprint(
						__("End Time ({0}) must be greater than Start Time ({1}).", [
							values.end_time,
							start_time,
						])
					);
					return;
				}
			}

			let cumulative = flt(frm.doc.total_completed_qty) + c;
			let excess_from_total = cumulative > flt(frm.doc.for_quantity)
				? cumulative - flt(frm.doc.for_quantity)
				: 0;
			let excess_from_cycle = c > m ? c - m : 0;
			let excess_qty = Math.max(excess_from_total, excess_from_cycle);
			let total_process_loss = flt(frm.doc.process_loss_qty) + l;

			dialog.hide();

			frappe.call({
				method: "taihan.taihan.job_card.update_excess_qty",
				args: {
					job_card: frm.doc.name,
					excess_qty: excess_qty,
					process_loss_qty: total_process_loss,
					pending_qty: p,
				},
				callback: function () {
					if (l > 0) {
						frm.set_value("process_loss_qty", total_process_loss);
					}
					frm.set_value("custom_pending_qty", p);

					if (excess_qty > 0) {
						frappe.show_alert({
							message: __(
								"Completed Qty exceeds target. Excess Qty of {0} recorded. Please follow Overproduction Approval.",
								[excess_qty]
							),
							indicator: "orange",
						});
					}

					const args = {
						job_card_id: frm.doc.name,
						complete_time: values.end_time || frappe.datetime.now_datetime(),
						status: "Complete",
						completed_qty: c,
						employee: values.employee,
					};
					frm.events.make_time_log(frm, args);
				},
			});
		},
	});

	dialog.show();
}

frappe.ui.form.on("Job Card Time Log", {
	time_logs_add: function (frm) {
		sync_time_logs_sequence(frm);
	},
	to_time: function (frm) {
		sync_time_logs_sequence(frm);
	},
	from_time: function (frm) {
		sync_time_logs_sequence(frm);
	},
});

function sync_time_logs_sequence(frm) {
	if (!frm.doc.time_logs || !frm.doc.time_logs.length) return;

	let creation_time = frm.doc.creation;
	let prev_to_time = null;

	frm.doc.time_logs.forEach((row, idx) => {
		if (idx === 0) {
			if (creation_time && row.from_time !== creation_time) {
				frappe.model.set_value(row.doctype, row.name, "from_time", creation_time);
			}
		} else {
			if (prev_to_time && row.from_time !== prev_to_time) {
				frappe.model.set_value(row.doctype, row.name, "from_time", prev_to_time);
			}
		}

		if (row.from_time && row.to_time) {
			let from_dt = moment(row.from_time);
			let to_dt = moment(row.to_time);
			let diff_mins = to_dt.diff(from_dt, "minutes", true);
			if (diff_mins >= 0 && Math.abs(flt(row.time_in_mins) - diff_mins) > 0.001) {
				frappe.model.set_value(row.doctype, row.name, "time_in_mins", diff_mins);
			}
		}
		prev_to_time = row.to_time;
	});

	frm.refresh_field("time_logs");
}



