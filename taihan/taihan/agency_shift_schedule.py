
import frappe
from frappe.model.document import Document

@frappe.whitelist()
def set_cancellation_remarks_agency(doctype, docname, remarks):
    frappe.db.sql("""
        UPDATE `tabAgency Shift Schedule`
        SET cancellation_remarks = %s
        WHERE name = %s
    """, (remarks, docname))
    
    frappe.db.commit()  # Ensure changes are committed before further checks
    
    doc = frappe.get_doc(doctype, docname)
    
    if not doc.cancellation_remarks:
        frappe.db.sql("""
        UPDATE `tabAgency Shift Schedule`
        SET docstatus = 1 , workflow_state = 'Approved'
        WHERE name = %s
    """, (docname))
        frappe.throw("Cancellation remarks are required before cancelling the document.")
    
    frappe.msgprint("Cancellation remarks updated successfully.")



@frappe.whitelist()
def reset_to_approved_agency(doctype, docname):
    doc = frappe.get_doc(doctype, docname)
    if doc.custom_status=="Completed":
        frappe.db.sql("""
            UPDATE `tabAgency Shift Schedule`
            SET docstatus = 1 , workflow_state = 'Approved'
            WHERE name = %s
        """, (docname))
        frappe.msgprint("The document has been reset to 'Approved' due to missing cancellation remarks.")
    else:
        frappe.db.sql("""
            UPDATE `tabAgency Shift Schedule`
            SET docstatus = 1 , workflow_state = 'Rejected'
            WHERE name = %s
        """, (docname))
        frappe.msgprint("The document has been reset to 'Rejected' due to missing cancellation remarks.")