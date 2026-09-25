import frappe
from frappe.model.document import Document



@frappe.whitelist()
def get_sales_person(converted_by):
    if converted_by:
        employee = frappe.db.exists("Employee", {"user_id": converted_by})
        if employee:
            sales_person = frappe.db.exists("Sales Person", {"employee": employee})
            commission_rate = frappe.db.get_value("Sales Person", sales_person, ["name", "commission_rate"])
            
            return commission_rate if commission_rate else 0
        


@frappe.whitelist()
def get_series_with_tax(date,company,doctype):
    company_series = frappe.db.get_value("Company Series",{'company':company,'document_type':doctype,'with_tax':1},'series')
    return company_series


@frappe.whitelist()
def get_series(date,company,doctype):
    company_series = frappe.db.get_value("Company Series",{'company':company,'document_type':doctype,'with_tax':0},'series')
    return company_series