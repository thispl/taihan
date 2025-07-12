// Copyright (c) 2025, Teampro and contributors
// For license information, please see license.txt

frappe.ui.form.on("Product Search", {
	item_code(frm){
		if(frm.doc.item_code){
			frm.call('get_data').then(r=>{
				if (r.message) {
					frm.fields_dict.perm.$wrapper.empty().append(r.message)
				}
			})	
		frm.call('get_data_taihan').then(j=>{
			if (j.message) {
				frm.fields_dict.html.$wrapper.empty().append(j.message)
			}
			
		})	
	}	
	},
});
