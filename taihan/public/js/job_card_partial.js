frappe.ui.form.on("Job Card", {
	refresh: function (frm) {
		bind_complete_job_button(frm);

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
		if (
			frm.doc.docstatus === 0 &&
			!frm.is_new() &&
			flt(frm.doc.custom_excess_qty) > 0
		) {
			let status = frm.doc.custom_overproduction_status || "";
			let is_approver = frappe.user.has_role("Overproduction Approver");

			if (!status || status === "Rejected") {
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

			if (status === "Pending" && is_approver) {
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
		}
	},
});

function bind_complete_job_button(frm) {
	if (frm.page && frm.page.wrapper && frm.page.wrapper[0]) {
		if (!frm._complete_job_interceptor_bound) {
			frm._complete_job_interceptor_bound = true;
			frm.page.wrapper[0].addEventListener(
				"click",
				function (e) {
					let target = e.target.closest("button, .btn");
					if (!target) return;
					let txt = (target.textContent || "").trim();
					if (txt === __("Complete Job") || txt === "Complete Job") {
						e.preventDefault();
						e.stopPropagation();
						e.stopImmediatePropagation();
						open_complete_job_dialog(frm);
					}
				},
				true
			);
		}
	}

	setTimeout(() => {
		let $buttons = frm.page.wrapper.find(".btn, button").filter(function () {
			let txt = $(this).text().trim();
			return txt === __("Complete Job") || txt === "Complete Job";
		});

		$buttons.each(function () {
			let $btn = $(this);
			$btn.off("click").on("click", function (e) {
				e.preventDefault();
				e.stopPropagation();
				e.stopImmediatePropagation();
				open_complete_job_dialog(frm);
			});
		});
	}, 100);
}

function open_complete_job_dialog(frm) {
	let remaining_qty = flt(frm.doc.for_quantity) - flt(frm.doc.total_completed_qty);
	if (remaining_qty < 0) remaining_qty = 0;

	let default_cycle_qty = remaining_qty > 0 ? remaining_qty : flt(frm.doc.for_quantity);
	let timezone =
		(frappe.boot.time_zone && (frappe.boot.time_zone.user || frappe.boot.time_zone.system)) ||
		"Asia/Kolkata";

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
				fieldname: "qty_to_manufacture",
				label: __("Qty to Manufacture in this Cycle"),
				fieldtype: "Float",
				reqd: 1,
				default: default_cycle_qty,
				description: __("Completed, Pending and Process Loss quantities must add up to this."),
				onchange: function () {
					let m = flt(dialog.get_value("qty_to_manufacture"));
					let c = flt(dialog.get_value("completed_qty"));
					let l = flt(dialog.get_value("process_loss_qty"));

					if (c + l > m) {
						c = Math.max(0, m - l);
						set_field_value(dialog, "completed_qty", c);
					}
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

					if (c + l > m) {
						let max_c = Math.max(0, m - l);
						frappe.msgprint(
							__(
								"Completed Quantity ({0}) cannot exceed Qty to Manufacture ({1}) minus Process Loss ({2}). Maximum allowed is {3}.",
								[c, m, l, max_c]
							)
						);
						c = max_c;
						set_field_value(dialog, "completed_qty", c);
					}

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

					if (c + l > m) {
						let max_l = Math.max(0, m - c);
						frappe.msgprint(
							__(
								"Process Loss Quantity ({0}) cannot exceed Qty to Manufacture ({1}) minus Completed Quantity ({2}). Maximum allowed is {3}.",
								[l, m, c, max_l]
							)
						);
						l = max_l;
						set_field_value(dialog, "process_loss_qty", l);
					}

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
			let m = flt(values.qty_to_manufacture);
			let c = flt(values.completed_qty);
			let p = flt(values.pending_qty);
			let l = flt(values.process_loss_qty);

			if (Math.abs(c + p + l - m) > 0.001) {
				frappe.msgprint(
					__(
						"Completed ({0}), Pending ({1}) and Process Loss ({2}) quantities must add up to Qty to Manufacture ({3}). Current sum is {4}.",
						[c, p, l, m, c + p + l]
					)
				);
				return;
			}

			if (c <= 0 && m > 0 && p === 0 && l === 0) {
				frappe.msgprint(__("Completed Quantity must be greater than 0."));
				return;
			}

			let remaining = flt(frm.doc.for_quantity) - flt(frm.doc.total_completed_qty);
			let excess_qty = c > remaining ? c - remaining : 0;
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

					const args = {
						job_card_id: frm.doc.name,
						complete_time: values.end_time || frappe.datetime.now_datetime(),
						status: "Complete",
						completed_qty: c,
					};
					frm.events.make_time_log(frm, args);
				},
			});
		},
	});

	dialog.show();
}


