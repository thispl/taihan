frappe.ui.form.on('Production Plan', {
    onload: function (frm) {
        update_visibility(frm);
    },

    refresh: function (frm) {
        update_visibility(frm);
    },

    custom_fiber_count: function (frm) {
        let val = flt(frm.doc.custom_fiber_count);
        if (val > 0) {
            if (val % 12 !== 0) {
                frm.set_value('custom_fiber_count', 0);
                frm.set_value('custom_no_of_colours', 0);
                frappe.msgprint(__('Fiber Count should be multiple of 12.'));
            } else {
                frm.set_value('custom_no_of_colours', Math.floor(val / 12));
            }
        } else {
            frm.set_value('custom_no_of_colours', 0);
        }
        update_visibility(frm);
    },

    custom_add_fiber_count: function (frm) {
        open_add_fiber_count_dialog(frm);
    },

    validate: function (frm) {
        let fiber_count = flt(frm.doc.custom_fiber_count);
        if (fiber_count > 0) {
            if (fiber_count % 12 !== 0) {
                frappe.msgprint(__('Fiber Count should be multiple of 12.'));
                frappe.validated = false;
                return false;
            }

            let expected_colours = Math.floor(fiber_count / 12);
            let tube_colors = (frm.doc.custom_tube_color || [])
                .map(d => d.tube_color)
                .filter(Boolean);

            let unique_colors = [...new Set(tube_colors)];
            if (unique_colors.length !== tube_colors.length) {
                frappe.msgprint(__('Duplicate tube colours are not allowed.'));
                frappe.validated = false;
                return false;
            }

            if (tube_colors.length !== expected_colours) {
                frappe.msgprint(__('Number of selected Tube Colours should be equal to No. of Colours.'));
                frappe.validated = false;
                return false;
            }
        }
    }
});

frappe.ui.form.on('Production Plan Item', {
    item_code: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (!row.bom_no) return;

        frappe.call({
            method: 'taihan.taihan.production_plan.get_operation_warehouse',
            args: {
                bom: row.bom_no
            },
            callback: function (r) {
                if (r.message) {
                    frappe.model.set_value(cdt, cdn, 'warehouse', r.message);
                }
            }
        });
    }
});

function update_visibility(frm) {
    let fiber_count = flt(frm.doc.custom_fiber_count);
    let has_fiber_count = fiber_count > 0;

    // 1. Fiber Count field: Read-only on the form, hidden when 0 or empty, shown when > 0
    frm.set_df_property('custom_fiber_count', 'read_only', 1);
    frm.toggle_display('custom_fiber_count', has_fiber_count);
    frm.set_df_property('custom_fiber_count', 'hidden', has_fiber_count ? 0 : 1);

    // 2. Button label: "Revise" if Fiber Count has value (> 0), "Add Fiber Count" if 0 or empty
    let btn_label = has_fiber_count ? __('Revise') : __('Add Fiber Count');
    frm.set_df_property('custom_add_fiber_count', 'label', btn_label);
    frm.toggle_display('custom_add_fiber_count', true);
    frm.set_df_property('custom_add_fiber_count', 'hidden', 0);
    frm.refresh_field('custom_add_fiber_count');

    // 3. Get Assembly / Get Sub Assembly button should be visible only when Fiber Count > 0
    frm.toggle_display('get_sub_assembly_items', has_fiber_count);
    frm.set_df_property('get_sub_assembly_items', 'hidden', has_fiber_count ? 0 : 1);
}

function open_add_fiber_count_dialog(frm) {
    let existing_colors = (frm.doc.custom_tube_color || [])
        .map(d => d.tube_color)
        .filter(Boolean);

    let current_fiber_count = flt(frm.doc.custom_fiber_count) || '';
    let current_no_of_colours = cint(frm.doc.custom_no_of_colours) || 0;
    let has_fiber_count = flt(frm.doc.custom_fiber_count) > 0;

    let dialog = new frappe.ui.Dialog({
        title: has_fiber_count ? __('Revise Fiber Count') : __('Add Fiber Count'),
        fields: [
            {
                fieldname: 'fiber_count',
                label: __('Fiber Count'),
                fieldtype: 'Int',
                default: current_fiber_count,
                reqd: 1,
                onchange: function () {
                    let val = dialog.get_value('fiber_count');
                    if (val === undefined || val === null || val === '') {
                        dialog.set_value('no_of_colours', 0);
                        return;
                    }
                    val = parseInt(val, 10);
                    if (isNaN(val) || val <= 0) {
                        dialog.set_value('no_of_colours', 0);
                        return;
                    }
                    if (val % 12 !== 0) {
                        dialog.set_value('fiber_count', 0);
                        dialog.set_value('no_of_colours', 0);
                        frappe.msgprint(__('Fiber Count should be multiple of 12.'));
                    } else {
                        dialog.set_value('no_of_colours', Math.floor(val / 12));
                    }
                }
            },
            {
                fieldname: 'no_of_colours',
                label: __('No. of Colours'),
                fieldtype: 'Int',
                read_only: 1,
                default: current_no_of_colours
            },
            {
                fieldname: 'tube_color',
                label: __('Tube Colour'),
                fieldtype: 'MultiSelectList',
                reqd: 1,
                get_data: function (txt) {
                    return frappe.db.get_link_options('Tube Colour', txt);
                }
            }
        ],
        primary_action_label: __('Save'),
        primary_action: function (values) {
            let fiber_count = parseInt(values.fiber_count, 10);
            let no_of_colours = parseInt(values.no_of_colours, 10);

            // Fiber Count Validation
            if (!fiber_count || isNaN(fiber_count) || fiber_count <= 0 || fiber_count % 12 !== 0) {
                frappe.msgprint(__('Fiber Count should be multiple of 12.'));
                dialog.set_value('fiber_count', 0);
                dialog.set_value('no_of_colours', 0);
                return;
            }

            let expected_colours = Math.floor(fiber_count / 12);
            if (no_of_colours !== expected_colours) {
                no_of_colours = expected_colours;
                dialog.set_value('no_of_colours', expected_colours);
            }

            // Extract Tube Colours
            let raw_colors = dialog.get_value('tube_color') || [];
            let selected_colors = [];
            if (Array.isArray(raw_colors)) {
                selected_colors = raw_colors
                    .map(c => (typeof c === 'object' && c !== null ? (c.value || c.label) : c))
                    .filter(Boolean);
            } else if (typeof raw_colors === 'string') {
                selected_colors = raw_colors
                    .split(',')
                    .map(c => c.trim())
                    .filter(Boolean);
            }

            // Validate duplicate colour selection
            let unique_colors = [...new Set(selected_colors)];
            if (unique_colors.length !== selected_colors.length) {
                frappe.msgprint(__('Duplicate colour selection is not allowed.'));
                return;
            }

            // Validate Tube Colour count matches No. of Colours
            if (selected_colors.length !== no_of_colours) {
                frappe.msgprint(__('Number of selected Tube Colours should be equal to No. of Colours.'));
                return;
            }

            // Apply values to form
            frm.set_value('custom_fiber_count', fiber_count);
            frm.set_value('custom_no_of_colours', no_of_colours);

            // Update custom_tube_color child table
            frm.clear_table('custom_tube_color');
            selected_colors.forEach(color => {
                let child = frm.add_child('custom_tube_color');
                child.tube_color = color;
            });
            frm.refresh_field('custom_tube_color');

            update_visibility(frm);
            frm.dirty();
            dialog.hide();
        }
    });

    dialog.show();

    // Pre-populate existing tube colors
    if (existing_colors && existing_colors.length > 0) {
        dialog.set_value('tube_color', existing_colors);
    }
}
