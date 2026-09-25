import frappe
from frappe.model.document import Document



@frappe.whitelist()
def update_barcode(doc,method):
    frappe.db.set_value("Quality Inspection",doc.name,"custom_machine_number",doc.batch_no)