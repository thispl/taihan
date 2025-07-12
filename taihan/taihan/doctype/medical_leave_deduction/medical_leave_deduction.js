// Copyright (c) 2025, Teampro and contributors
// For license information, please see license.txt

frappe.ui.form.on("Medical Leave Deduction", {
	update_salary(frm) {
        frappe.call({
            method:"taihan.taihan.doctype.medical_leave_deduction.medical_leave_deduction.leave_deduction",
            args:{
                from_date:frm.doc.from_date,
                to_date:frm.doc.to_date
            },
            callback(r){
                
            }
        })
	},
});
