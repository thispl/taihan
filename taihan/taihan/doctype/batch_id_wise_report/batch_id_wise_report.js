// Copyright (c) 2025, Teampro and contributors
// For license information, please see license.txt

frappe.ui.form.on("Batch ID Wise Report", {
	track_download(frm) {
		if (!frm.doc.jacketing_batch) {
			frappe.msgprint(__("Please enter Jacketing Batch"));
			return;
		}
		let url = frappe.urllib.get_full_url(
			"/api/method/taihan.taihan.doctype.batch_id_wise_report.batch_id_wise_report.download_tracking?jacketing_batch=" + encodeURIComponent(frm.doc.jacketing_batch)
		);
		window.open(url);
	}
});
