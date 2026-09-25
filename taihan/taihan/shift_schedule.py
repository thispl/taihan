import frappe
from frappe.model.document import Document

@frappe.whitelist()
def set_cancellation_remarks_shift_schedule(doctype, docname, remarks):
    frappe.db.sql("""
        UPDATE `tabShift Schedule`
        SET cancellation_remarks = %s
        WHERE name = %s
    """, (remarks, docname))
    
    frappe.db.commit()  # Ensure changes are committed before further checks
    
    doc = frappe.get_doc(doctype, docname)
    
    if not doc.cancellation_remarks:
        frappe.db.sql("""
        UPDATE `tabShift Schedule`
        SET docstatus = 1 , workflow_state = 'Approved'
        WHERE name = %s
    """, (docname))
        frappe.throw("Cancellation remarks are required before cancelling the document.")
    
    frappe.msgprint("Cancellation remarks updated successfully.")


@frappe.whitelist()
def reset_to_approved__shift_schedule(doctype, docname):
    doc = frappe.get_doc(doctype, docname)
    if doc.custom_status=="Completed":
        frappe.db.sql("""
            UPDATE `tabShift Schedule`
            SET docstatus = 1 , workflow_state = 'Approved'
            WHERE name = %s
        """, (docname))
        frappe.msgprint("The document has been reset to 'Approved' due to missing cancellation remarks.")
    else:
        frappe.db.sql("""
            UPDATE `tabShift Schedule`
            SET docstatus = 1 , workflow_state = 'Rejected'
            WHERE name = %s
        """, (docname))
        frappe.msgprint("The document has been reset to 'Rejected' due to missing cancellation remarks.")


from frappe.utils import  formatdate,get_last_day, get_first_day, add_days
#Set default to date is based on given from date(Report filters)
@frappe.whitelist()
def get_to_date(from_date):
    return get_last_day(from_date)