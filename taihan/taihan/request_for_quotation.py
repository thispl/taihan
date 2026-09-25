

import frappe
from frappe.utils.pdf import get_pdf
from frappe.utils.file_manager import save_file

@frappe.whitelist()
def send_rfq_pdf(doc,method):
    doc = frappe.get_doc("Request for Quotation", doc.name)
    
    if not doc.suppliers:
        frappe.msgprint("No suppliers found in the RFQ.", alert=True, indicator="red")
        return

    subject = f"Request for Quotation: {doc.name}"
    sent_emails = []
    generated_pdfs = []

    for supplier in doc.suppliers:
        if not supplier.email_id:
            continue  # Skip if no email
        address = frappe.db.get_value('Address', {'address_title': "Taihan Kuwait Fiber Optic Cable", 'is_your_company_address': 1}, ['address_line1', 'address_line2', 'city', 'country', 'phone', 'email_id', 'pincode'], as_dict=True)
        context = {
            "address": address,
            "doc": doc,
            "supplier": supplier.supplier,
            "supplier_email": supplier.email_id
        }
        html_content = frappe.render_template("taihan/templates/rfq_teamplate.html", context)
        pdf_data = get_pdf(html_content)
        file_name = f"RFQ_{doc.name}_{supplier.supplier}.pdf"
        save_file(file_name, pdf_data, doc.doctype, doc.name, is_private=1)
        generated_pdfs.append(file_name)

        message = f"""
        Dear {supplier.supplier_name},<br><br>
        Please find the attached Request for Quotation <b>{doc.name}</b>.<br>
        Kindly review and provide your best quote.<br><br>
        Regards,<br>{frappe.db.get_single_value("Global Defaults", "default_company")}
        """
        frappe.sendmail(
            recipients=[supplier.email_id],
            subject=subject,
            message=message,
            attachments=[{"fname": file_name, "fcontent": pdf_data}]
        )

        sent_emails.append(supplier.email_id)
    if sent_emails:
        frappe.msgprint(f"Emails sent to: {', '.join(sent_emails)}", alert=True, indicator="green")