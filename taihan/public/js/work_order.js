frappe.ui.form.on('Work Order', {
    refresh: function (frm) {
        frm.events.make_job_card = function (frm) {
            open_custom_job_card_dialog(frm);
        };

        if (frm.page && frm.page.wrapper && frm.page.wrapper[0]) {
            if (!frm._create_jc_interceptor_bound) {
                frm._create_jc_interceptor_bound = true;
                frm.page.wrapper[0].addEventListener(
                    "click",
                    function (e) {
                        let target = e.target.closest("button, .btn");
                        if (!target) return;
                        let txt = (target.textContent || "").trim();
                        if (txt === __("Create Job Card") || txt === "Create Job Card") {
                            e.preventDefault();
                            e.stopPropagation();
                            e.stopImmediatePropagation();
                            open_custom_job_card_dialog(frm);
                        }
                    },
                    true
                );
            }
        }
    },
    make_job_card: function (frm) {
        open_custom_job_card_dialog(frm);
    },
    production_plan: function (frm) {
        if (frm.doc.production_plan) {
            frm.set_value('custom_fiber_count', 12);
        }
    },
    production_plan_sub_assembly_item: function (frm) {
        if (frm.doc.production_plan_sub_assembly_item) {
            frappe.db.get_value(
                'Production Plan Sub Assembly Item',
                frm.doc.production_plan_sub_assembly_item,
                'custom_tube_colour',
                function (r) {
                    if (r && r.custom_tube_colour) {
                        frm.set_value('custom_tube_color', r.custom_tube_colour);
                    }
                }
            );
        }
    }
});

function open_custom_job_card_dialog(frm) {
    let pending_operations = [];
    (frm.doc.operations || []).forEach((data) => {
        let op_qty = flt(frm.doc.qty);
        pending_operations.push({
            name: data.name,
            operation: data.operation,
            workstation: data.workstation || "",
            sequence_id: data.sequence_id || 1,
            batch_size: data.batch_size || 0,
            workstation_type: data.workstation_type || "",
            hour_rate: data.hour_rate || 0,
            pending_qty: op_qty,
            qty: op_qty,
            use_column_plan: false,
            no_of_job_cards: null,
            column_quantities: []
        });
    });

    if (!pending_operations.length) {
        frappe.msgprint(__("No operations found in this Work Order."));
        return;
    }

    show_job_card_dialog(frm, pending_operations);
}

function show_job_card_dialog(frm, pending_operations) {
    let dialog = new frappe.ui.Dialog({
        title: __("Create Job Card"),
        size: "large",
        fields: [
            {
                fieldtype: "HTML",
                fieldname: "operations_html"
            }
        ],
        primary_action_label: __("Create"),
        primary_action: function () {
            // Validation
            for (let i = 0; i < pending_operations.length; i++) {
                let op = pending_operations[i];
                if (op.use_column_plan) {
                    let num_cards = parseInt(op.no_of_job_cards);
                    if (!num_cards || num_cards <= 0) {
                        frappe.msgprint(
                            __("Please enter a valid positive <b>No. of Job Cards</b> for Operation: <b>{0}</b>", [op.operation])
                        );
                        return;
                    }

                    if (!op.column_quantities || op.column_quantities.length !== num_cards) {
                        frappe.msgprint(
                            __("The number of column quantities ({0}) does not match No. of Job Cards ({1}) for Operation: <b>{2}</b>", [
                                op.column_quantities ? op.column_quantities.length : 0,
                                num_cards,
                                op.operation
                            ])
                        );
                        return;
                    }

                    for (let c = 0; c < op.column_quantities.length; c++) {
                        let q = flt(op.column_quantities[c]);
                        if (isNaN(q) || q < 0) {
                            frappe.msgprint(
                                __("Column {0} quantity cannot be negative or invalid for Operation: <b>{1}</b>", [c + 1, op.operation])
                            );
                            return;
                        }
                    }

                    let sum = op.column_quantities.reduce((acc, v) => acc + flt(v), 0);
                    let target_qty = flt(op.qty);

                    if (Math.abs(sum - target_qty) > 0.001) {
                        frappe.msgprint(
                            __(
                                "Column Plan quantity must be equal to Manufactured Qty for Operation: <b>{0}</b><br><br>" +
                                "<b>Manufactured Qty:</b> {1}<br>" +
                                "<b>Column Plan Total:</b> {2}",
                                [op.operation, target_qty, sum]
                            )
                        );
                        return;
                    }
                } else {
                    let standard_qty = flt(op.qty);
                    if (standard_qty <= 0) {
                        frappe.msgprint(
                            __("Quantity to Manufacture must be greater than 0 for Operation: <b>{0}</b>", [op.operation])
                        );
                        return;
                    }
                    if (standard_qty > flt(op.pending_qty)) {
                        frappe.msgprint(
                            __("Quantity to Manufacture ({0}) cannot exceed Pending Qty ({1}) for Operation: <b>{2}</b>", [
                                standard_qty,
                                op.pending_qty,
                                op.operation
                            ])
                        );
                        return;
                    }
                }
            }

            // All validations passed -> Call Backend
            dialog.hide();
            frappe.call({
                method: "taihan.taihan.work_order.make_job_cards_with_column_plan",
                freeze: true,
                freeze_message: __("Creating Job Cards..."),
                args: {
                    work_order: frm.doc.name,
                    operations: pending_operations
                },
                callback: function (r) {
                    if (r.message) {
                        frappe.show_alert({
                            message: __("{0} Job Card(s) created successfully.", [r.message.length]),
                            indicator: "green"
                        });
                    }
                    frm.reload_doc();
                }
            });
        }
    });

    function calculate_column_split(target_qty, num_cards) {
        if (!num_cards || num_cards <= 0) return [];
        let base_qty = Math.floor(target_qty / num_cards);
        let last_qty = target_qty - (base_qty * (num_cards - 1));
        let list = [];
        for (let i = 0; i < num_cards - 1; i++) {
            list.push(base_qty);
        }
        list.push(last_qty);
        return list;
    }

    function get_grid_inner_html(op, idx) {
        let total_col_qty = (op.column_quantities || []).reduce((acc, v) => acc + flt(v), 0);
        let target_qty = flt(op.qty);
        let is_matched = Math.abs(total_col_qty - target_qty) < 0.001;

        return `
            <div class="table-responsive" style="overflow-x: auto; border: 1px solid var(--border-color, #e2e8f0); border-radius: 4px; background: var(--control-bg, #f8fafc);">
                <table class="table table-bordered table-sm m-0 text-center" style="table-layout: fixed; width: max-content; min-width: 100%;">
                    <thead>
                        <tr style="background: var(--table-header-bg, #f1f5f9);">
                            ${(op.column_quantities || []).map((_, c_idx) => `
                                <th style="padding: 6px 8px; width: 85px; font-size: 12px; font-weight: 600; color: var(--text-color, #334155);">
                                    C${c_idx + 1}
                                </th>
                            `).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            ${(op.column_quantities || []).map((val, c_idx) => `
                                <td style="padding: 4px;">
                                    <input type="number" step="any" min="0" class="form-control form-control-sm col-qty-input text-center font-weight-bold" data-op-idx="${idx}" data-col-idx="${c_idx}" value="${val}" style="height: 30px; font-size: 13px; border-color: #cbd5e1;">
                                </td>
                            `).join('')}
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- Live Calculation & Validation Status Footer -->
            <div class="d-flex flex-wrap justify-content-between align-items-center mt-2 px-1 pt-1">
                <div class="small">
                    <span class="text-muted">${__('Column Plan Total')}:</span>
                    <b class="ml-1 total-col-display-${idx}" style="font-size: 14px; color: ${is_matched ? '#16a34a' : '#dc2626'};">${total_col_qty}</b>
                    <span class="text-muted ml-3">${__('Manufactured Qty')}:</span>
                    <b class="ml-1 text-dark" style="font-size: 14px;">${target_qty}</b>
                </div>
                <div class="status-badge-${idx}">
                    ${is_matched ?
                        `<span class="badge badge-success px-2 py-1" style="font-size: 12px;"><i class="fa fa-check mr-1"></i>${__('Quantity matched')}</span>` :
                        `<span class="badge badge-danger px-2 py-1" style="font-size: 12px;"><i class="fa fa-times mr-1"></i>${__('Quantity mismatch')} (${total_col_qty} / ${target_qty})</span>`
                    }
                </div>
            </div>
        `;
    }

    function render_op_grid(idx) {
        let op = pending_operations[idx];
        let $wrapper = dialog.fields_dict.operations_html.$wrapper;
        let $grid_sec = $wrapper.find(`.cp-grid-section-${idx}`);

        if (!op.use_column_plan || !op.no_of_job_cards || op.no_of_job_cards <= 0) {
            $grid_sec.hide().empty();
            return;
        }

        $grid_sec.html(get_grid_inner_html(op, idx)).show();
        bind_col_qty_events(idx);
    }

    function bind_col_qty_events(idx) {
        let $wrapper = dialog.fields_dict.operations_html.$wrapper;
        let selector = typeof idx !== 'undefined' ? `.col-qty-input[data-op-idx="${idx}"]` : '.col-qty-input';

        $wrapper.find(selector).off('input').on('input', function () {
            let op_idx = parseInt($(this).data('op-idx'));
            let col_idx = parseInt($(this).data('col-idx'));
            let val = flt($(this).val());

            pending_operations[op_idx].column_quantities[col_idx] = val;

            let total_col_qty = (pending_operations[op_idx].column_quantities || []).reduce((acc, v) => acc + flt(v), 0);
            let target_qty = flt(pending_operations[op_idx].qty);
            let is_matched = Math.abs(total_col_qty - target_qty) < 0.001;

            $wrapper.find(`.total-col-display-${op_idx}`)
                .text(total_col_qty)
                .css('color', is_matched ? '#16a34a' : '#dc2626');

            let badge_html = is_matched ?
                `<span class="badge badge-success px-2 py-1" style="font-size: 12px;"><i class="fa fa-check mr-1"></i>${__('Quantity matched')}</span>` :
                `<span class="badge badge-danger px-2 py-1" style="font-size: 12px;"><i class="fa fa-times mr-1"></i>${__('Quantity mismatch')} (${total_col_qty} / ${target_qty})</span>`;

            $wrapper.find(`.status-badge-${op_idx}`).html(badge_html);
        });
    }

    function render_ui() {
        let html = `
            <div class="column-plan-container" style="max-height: 65vh; overflow-y: auto; padding: 5px;">
                <!-- Column Plan Purpose Banner -->
                <div class="alert alert-info py-2 px-3 mb-3 d-flex align-items-start" style="font-size: 13px; background-color: #f0f9ff; border: 1px solid #bae6fd; color: #0369a1; border-radius: 6px;">
                    <i class="fa fa-info-circle mr-2 mt-1" style="font-size: 15px; color: #0284c7;"></i>
                    <div>
                        <strong>Column Plan:</strong> Enable this option on any operation to distribute its manufactured quantity across multiple Job Cards with customized quantities per card.
                    </div>
                </div>
        `;

        pending_operations.forEach((op, idx) => {
            let target_qty = flt(op.qty);

            html += `
                <div class="operation-plan-card mb-4 p-3 border rounded" data-op-idx="${idx}" style="background: var(--card-bg, #ffffff); border-color: var(--border-color, #d1d8dd); box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                    <!-- Header -->
                    <div class="d-flex justify-content-between align-items-center mb-3 pb-2 border-bottom">
                        <div>
                            <h5 class="m-0 font-weight-bold" style="color: var(--text-color, #1f272e);">
                                ${escape_html(op.operation)}
                            </h5>
                            <small class="text-muted">${op.workstation ? __('Workstation: ') + escape_html(op.workstation) : ''}</small>
                        </div>
                        <div class="text-right">
                            <span class="text-muted small">${__('Manufactured Qty')}:</span>
                            <span class="font-weight-bold ml-1 text-primary" style="font-size: 15px;">${target_qty}</span>
                        </div>
                    </div>

                    <!-- Options Row -->
                    <div class="row align-items-center">
                        <!-- High Visibility Checkbox -->
                        <div class="col-sm-6 mb-2 mb-sm-0">
                            <div class="d-flex align-items-center">
                                <input type="checkbox" class="cp-toggle" id="cp_toggle_${idx}" data-op-idx="${idx}" ${op.use_column_plan ? 'checked' : ''} style="width: 16px; height: 16px; cursor: pointer; accent-color: #2563eb; margin: 0 8px 0 0;">
                                <label for="cp_toggle_${idx}" style="cursor: pointer; margin: 0; font-size: 13px; font-weight: 600; color: var(--text-color, #1f272e); user-select: none;">
                                    ${__('Column Plan')}
                                </label>
                            </div>
                            <small class="text-muted d-block mt-1">${__('Split quantity into multiple custom Job Cards')}</small>
                        </div>

                        <!-- Standard Quantity (when Column Plan is unchecked) -->
                        <div class="col-sm-6 std-section-${idx}" style="${op.use_column_plan ? 'display: none;' : ''}">
                            <div class="d-flex align-items-center justify-content-sm-end">
                                <label class="small text-muted m-0 mr-2">${__('Quantity to Manufacture')}:</label>
                                <input type="number" step="any" min="0" max="${op.pending_qty}" class="form-control form-control-sm std-qty-input" data-op-idx="${idx}" value="${op.qty}" style="max-width: 130px;">
                            </div>
                        </div>

                        <!-- No. of Job Cards Input (when Column Plan is checked) -->
                        <div class="col-sm-6 cp-count-section-${idx}" style="${!op.use_column_plan ? 'display: none;' : ''}">
                            <div class="d-flex align-items-center justify-content-sm-end">
                                <label class="small font-weight-bold m-0 mr-2 text-nowrap">${__('No. of Job Cards')}:</label>
                                <input type="number" min="1" step="1" class="form-control form-control-sm num-cards-input" data-op-idx="${idx}" value="${op.no_of_job_cards || ''}" placeholder="e.g. 10" style="max-width: 110px;">
                                <button type="button" class="btn btn-xs btn-default ml-2 btn-reset-split" data-op-idx="${idx}" title="${__('Reset to Equal Split')}">
                                    <i class="fa fa-refresh mr-1"></i>${__('Split')}
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- Column Plan Grid Container -->
                    <div class="cp-grid-section-${idx} mt-3 pt-3 border-top" style="${!op.use_column_plan || !op.no_of_job_cards ? 'display: none;' : ''}">
                        ${op.use_column_plan && op.no_of_job_cards ? get_grid_inner_html(op, idx) : ''}
                    </div>
                </div>
            `;
        });

        html += `</div>`;
        dialog.fields_dict.operations_html.$wrapper.html(html);
        bind_dialog_events();
    }

    function bind_dialog_events() {
        let $wrapper = dialog.fields_dict.operations_html.$wrapper;

        // Toggle Column Plan Checkbox
        $wrapper.find('.cp-toggle').off('change').on('change', function () {
            let op_idx = parseInt($(this).data('op-idx'));
            let checked = this.checked;
            pending_operations[op_idx].use_column_plan = checked;

            if (checked) {
                $wrapper.find(`.std-section-${op_idx}`).hide();
                $wrapper.find(`.cp-count-section-${op_idx}`).show();
                if (!pending_operations[op_idx].no_of_job_cards) {
                    let default_n = pending_operations[op_idx].qty >= 10 ? 10 : Math.max(1, Math.floor(pending_operations[op_idx].qty));
                    pending_operations[op_idx].no_of_job_cards = default_n;
                    pending_operations[op_idx].column_quantities = calculate_column_split(
                        flt(pending_operations[op_idx].qty),
                        default_n
                    );
                    $wrapper.find(`.num-cards-input[data-op-idx="${op_idx}"]`).val(default_n);
                }
            } else {
                $wrapper.find(`.std-section-${op_idx}`).show();
                $wrapper.find(`.cp-count-section-${op_idx}`).hide();
            }

            render_op_grid(op_idx);
        });

        // Change Standard Quantity (when Column Plan is off)
        $wrapper.find('.std-qty-input').off('input change').on('input change', function () {
            let op_idx = parseInt($(this).data('op-idx'));
            let val = flt($(this).val());
            pending_operations[op_idx].qty = val;
        });

        // Change No. of Job Cards without losing input focus!
        $wrapper.find('.num-cards-input').off('input change').on('input change', function () {
            let op_idx = parseInt($(this).data('op-idx'));
            let num = parseInt($(this).val());
            pending_operations[op_idx].no_of_job_cards = num;
            if (num > 0) {
                pending_operations[op_idx].column_quantities = calculate_column_split(
                    flt(pending_operations[op_idx].qty),
                    num
                );
            } else {
                pending_operations[op_idx].column_quantities = [];
            }
            render_op_grid(op_idx);
        });

        // Reset Split Button
        $wrapper.find('.btn-reset-split').off('click').on('click', function () {
            let op_idx = parseInt($(this).data('op-idx'));
            let num = parseInt(pending_operations[op_idx].no_of_job_cards) || 1;
            pending_operations[op_idx].column_quantities = calculate_column_split(
                flt(pending_operations[op_idx].qty),
                num
            );
            render_op_grid(op_idx);
        });

        // Bind column qty inputs for initially rendered grids
        bind_col_qty_events();
    }

    dialog.show();
    render_ui();
}

function escape_html(str) {
    if (!str) return '';
    return $('<div>').text(str).html();
}

