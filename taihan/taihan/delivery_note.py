import frappe
from frappe.model.document import Document



@frappe.whitelist()
def set_inspected_by(doc, method):
    doc.inspected_by = frappe.session.user



@frappe.whitelist()
def get_series(date,company,doctype):
    company_series = frappe.db.get_value("Company Series",{'company':company,'document_type':doctype,'with_tax':0},'series')
    return company_series