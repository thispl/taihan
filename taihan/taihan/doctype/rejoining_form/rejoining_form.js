frappe.ui.form.on('Rejoining Form', {
    before_workflow_action: async (frm) => {
        if (frm.doc.workflow_state === "Pending for HR Manager" || frm.doc.workflow_state == "Pending for HOD" ) {
            if (frm.selected_workflow_action === "Reject") {
                frappe.validated = false;
                let d = new frappe.ui.Dialog({
                    title: 'Provide Rejection Remarks',
                    fields: [
                        {
                            label: 'Rejection Remarks',
                            fieldname: 'rejection_remarks',
                            fieldtype: 'Small Text',
                            reqd: 1
                        }
                    ],
                    primary_action_label: 'Reject',
                    primary_action: async (values) => {
                        let remarks = values.rejection_remarks?.trim();
                        frm.set_value('remarks', remarks);
                        if (!remarks) {
                            frappe.msgprint(__('Rejection remarks are required.'));
                            frappe.validated = false;
                            return;
                        }

                        d.hide();
                        await frm.set_value('remarks', remarks);
                        await frm.set_value('workflow_state', "Rejected");
                        await frm.save();
                        frappe.validated = true; 
                        frm.reload_doc();
                    }
                });
                d.show();
            }
        }
        if (frm.doc.workflow_state === "Approved" || frm.doc.workflow_state === "Rejected") {
            if (frm.selected_workflow_action === "Cancel") {
                frappe.validated = false;
        
                let d = new frappe.ui.Dialog({
                    title: 'Provide Cancellation Remarks',
                    fields: [
                        {
                            label: 'Cancellation Remarks',
                            fieldname: 'cancellation_remarks',
                            fieldtype: 'Small Text',
                            reqd: 1
                        }
                    ],
                    // Prevent closing the dialog when clicking outside
                    // static: true,
                    primary_action_label: 'Cancel',
                    primary_action: async (values) => {
                        let remarks = values.cancellation_remarks?.trim();
                        
                        if (!remarks) {
                            frappe.msgprint(__('Cancellation remarks are required.'));
                            return;
                        }
        
                        d.hide();
        
                        frappe.call({
                            method: "taihan.taihan.rejoining_form.set_cancellation_remarks",
                            args: {
                                doctype: frm.doc.doctype,
                                docname: frm.doc.name,
                                remarks: remarks
                            },
                            callback: function (response) {
                                if (!response.exc) {
                                    frappe.validated = true;  // Allow cancellation after remarks are set
                                    frm.reload_doc();
                                }
                            }
                        });
                    }
                });
        
                d.show();
        
                // If the user tries to close without entering remarks, reset the state
                d.$wrapper.on('hidden.bs.modal', function () {
                    let remarks = d.get_value('cancellation_remarks')?.trim();
                    if (!remarks) {
                        frappe.msgprint(__('Cancellation remarks are required before cancelling. The document will remain in Approved state.'));   
                        frappe.call({
                            method: "taihan.taihan.rejoining_form.reset_to_approved",  // Backend method to reset state
                            args: {
                                doctype: frm.doc.doctype,
                                docname: frm.doc.name
                            },
                            callback: function () {
                                frm.reload_doc();
                            }
                        });
                    }
                });
            }
        }
        
        
    }
    
});
