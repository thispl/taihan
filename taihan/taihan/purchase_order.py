import frappe
from frappe.model.document import Document

#General Settings Code 
@frappe.whitelist()
def get_series(date,company,doctype):
    company_series = frappe.db.get_value("Company Series",{'company':company,'document_type':doctype,'with_tax':0},'series')
    return company_series