from __future__ import unicode_literals
import frappe,erpnext
from frappe.utils import cint
from frappe.utils import flt, fmt_money
import json
from frappe.utils import date_diff, add_months,today,add_days,add_years,nowdate,flt
from frappe.utils import cstr, cint, getdate,get_first_day, get_last_day, today, time_diff_in_hours

from frappe.model.mapper import get_mapped_doc
from frappe.utils.file_manager import get_file
from frappe.utils.csvutils import UnicodeWriter, read_csv_content
import datetime
from datetime import date,datetime,timedelta
import openpyxl
from collections import defaultdict
from openpyxl import Workbook
import openpyxl
import xlrd
import re
from frappe.utils import date_diff,today,cstr
from datetime import datetime
from dateutil import relativedelta
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import GradientFill, PatternFill
from frappe.utils import formatdate


from erpnext.setup.utils import get_exchange_rate
from frappe import throw,_, db, get_doc, throw, whitelist


from frappe.utils import (
    add_days,
    cint,
    cstr,
    date_diff,
    flt,
    formatdate,
    get_first_day,
    get_link_to_form,
    getdate,
    money_in_words,
    rounded,
)



# # update employee expense in MIS while cancel Journal Entry
# @frappe.whitelist()
# def update_expenses_cancel(doc,method):
#     if doc.voucher_type=="Journal Entry":
#         if doc.accounts:
#             for i in doc.accounts:
#                 if i.account=="Employee Joining Expense - TKFCCD" and i.party_type=="Employee":
#                     emp=frappe.get_doc("Employee",{"name":i.party})
#                     emp.custom_expense = [
#                             row for row in emp.custom_expense if row.journal_entry != doc.name
#                         ]
#                     for idx, row in enumerate(emp.custom_expense, start=1):
#                         row.idx = idx
#                     emp.save()
#     frappe.db.commit()

# #Employee should apply for leave before 30 days when leave type is not leave without pay(not for HR User, HR Manger and HOD) and it will allow when is leave without pay is checked in leave type
# @frappe.whitelist()
# def validate_leave_application(doc, method):
#     today = frappe.utils.today()
#     leave_start_date = doc.from_date

#     lwp_leave_types = frappe.db.get_all("Leave Type", filters={"is_lwp": 0})
#     user_roles = frappe.get_roles(frappe.session.user)

#     roles = ["HR User", "HR Manager", "HOD"]

#     if not any(role in user_roles for role in roles):
#         days_diff = frappe.utils.date_diff(leave_start_date, today)

#         for l in lwp_leave_types:
#             if l["name"] == doc.leave_type:
#                 if days_diff < 30:
#                     frappe.throw("Employees should apply for leave at least 30 days in advance.")

# @frappe.whitelist()
# def continuous_leave_without_information():
#     job = frappe.db.exists('Scheduled Job Type', 'create_umrah_leave')
#     if not job:
#         sjt = frappe.new_doc("Scheduled Job Type")
#         sjt.update({
#             "method": 'taihan.custom.create_umrah_leave',
#             "frequency": 'Cron',
#             # "cron_format": '* * * 1 *'
#             "cron_format":'0 0 1 1 *'
#         })
#         sjt.save(ignore_permissions=True)


                
# @frappe.whitelist()
# def check_discount_percent(discount, customer):
#     # Get max discount allowed for the user from "Sales Settings"
#     max_discount = 0
#     user_discount = frappe.db.get_value("Quotation Discount", {'user': frappe.session.user, 'parent': 'Sales Settings'}, 'max_dis')
    
#     if user_discount:
#         max_discount = float(user_discount)

#     # If user has no discount privilege
#     if max_discount == 0:
#         return "invalid"

#     # If entered discount exceeds user's max discount, check customer-specific discount
#     if float(discount) > max_discount:
#         customer_discount = frappe.db.get_value("Customer", {'name': customer}, 'custom_max_percentage')
#         if customer_discount:
#             print("hi")
#             customer_discount = float(customer_discount)
#             if float(discount) <= customer_discount:
#                 max_discount = customer_discount  # Allow if within customer-specific limit
#             else:
#                 return customer_discount  # Notify the limit set for the customer
#         else:
#             return max_discount  # Notify the general max limit for the user

#     return ""


# validate Hajj leave allocation 
@frappe.whitelist()
def validate_hajj_allocation(employee,leave_type,name):
    if frappe.db.exists("Leave Allocation",{"employee":employee,"leave_type":leave_type,"docstatus":("!=",2),"name":("!=",name)}):
        return True
    return False



# Automatic creation for Umrah leave allocation 4 days for every year (Active employees)
# @frappe.whitelist()
# def create_umrah_leave():
#     date = today()
#     from_date = get_first_day(date)  # First day of the current year
#     year = from_date.year 
#     to_date = f"{year}-12-31"
#     active_employees = frappe.get_all("Employee", {"status": "Active"}, ["name"])
#     for employee in active_employees:
#         leave_allocation_exists = frappe.db.exists(
#             "Leave Allocation",
#             {
#                 "employee": employee.name,
#                 "leave_type": "Umrah Leave",
#                 "from_date": from_date,
#                 "to_date": to_date,
#             }
#         )
#         if not leave_allocation_exists:
#             leave_allocation = frappe.new_doc("Leave Allocation")
#             leave_allocation.employee = employee.name
#             leave_allocation.leave_type = "Umrah Leave"
#             leave_allocation.from_date = from_date
#             leave_allocation.to_date = to_date  # Last day of the current year
#             leave_allocation.new_leaves_allocated = 4
#             leave_allocation.total_leaves_allocated = 4
#             leave_allocation.submit()
#     frappe.db.commit()


    
# validate the discount percentage based on roles in sales settings in quotation client script
# @frappe.whitelist()
# def check_discount_percent(discount):
#     user_roles = frappe.get_roles(frappe.session.user)
#     max_discount = 0
#     for role in user_roles:
#         d = frappe.db.get_value("Quotation Discount", {'role':role, 'parent': 'Sales Settings'}, ['role', 'max_dis'])
#         if d:
#             if max_discount < d[1]:
#                 max_discount = d[1]
    
#     if max_discount == 0:
#         return 'invalid'
#     if float(discount) > max_discount:
#         frappe.throw("Maximum discount percentage allowed for you is %s%% "%(int(max_discount)))
            
# # validate the discount percentage based on roles in sales settings in quotation hooks
# @frappe.whitelist()
# def validate_check_discount_percent(doc,method):
# 	user_roles = frappe.get_roles(frappe.session.user)
# 	max_discount = 0
# 	for role in user_roles:
# 		d = frappe.db.get_value("Quotation Discount", {'role':role, 'parent': 'Sales Settings'}, ['role', 'max_dis'])
# 		if d:
# 			if max_discount < d[1]:
# 				max_discount = d[1]
    
# 	if max_discount == 0:
# 		return 'invalid'
# 	if float(doc.additional_discount_percentage) > max_discount:
# 		frappe.throw("Maximum discount percentage allowed for you is %s%% "%(int(max_discount)))


from frappe.utils import  formatdate,get_last_day, get_first_day, add_days
#Set default to date is based on given from date(Report filters)
@frappe.whitelist()
def get_to_date(from_date):
    return get_last_day(from_date)
    
# # update role based notification for quotation discount %
# @frappe.whitelist()
# def quotation_notification(doc,method):
#     user_roles = frappe.get_roles(frappe.session.user)
#     max_discount = 0
#     approver_role = None

#     # Define role hierarchy
#     role_hierarchy = {
#         "Sales User": "Sales Manager",
#         "Sales Manager": "Sales Master Manager",
#         "Sales Master Manager": None  # No approval needed
#     }

#     for role in user_roles:
#         d = frappe.db.get_value("Quotation Discount", {'role': role, 'parent': 'Sales Settings'}, ['role', 'max_dis'])
#         if d:
#             if max_discount < d[1]:  # Take the max allowed discount among roles
#                 max_discount = d[1]
#                 approver_role = role_hierarchy.get(role)

#     if max_discount == 0:
#         return 'invalid'
#     if doc.additional_discount_percentage:
#         if float(doc.additional_discount_percentage) > max_discount:
#             doc.custom_role = 1  # Set custom_role before throwing an exception
#             frappe.msgprint(f"Discount exceeds allowed limit. Approval required from {approver_role}.")
#         else:
#             doc.custom_role=0
#     else:
#         doc.custom_role=0

# # validate the quotation while submit the quotation
# @frappe.whitelist()
# def quotation_notification_before_submit(doc,method):
#     user_roles = frappe.get_roles(frappe.session.user)
#     max_discount = 0
#     approver_role = None

#     # Define role hierarchy
#     role_hierarchy = {
#         "Sales User": "Sales Manager",
#         "Sales Manager": "Sales Master Manager",
#         "Sales Master Manager": None  # No approval needed
#     }

#     for role in user_roles:
#         d = frappe.db.get_value("Quotation Discount", {'role': role, 'parent': 'Sales Settings'}, ['role', 'max_dis'])
#         if d:
#             if max_discount < d[1]: 
#                 max_discount = d[1]
#                 approver_role = role_hierarchy.get(role)

#     if max_discount == 0:
#         return 'invalid'

#     if doc.custom_role==1:
#         frappe.throw(f"Maximum discount percentage allowed for you is {int(max_discount)}%.Discount exceeds allowed limit. Approval required from {approver_role}.")

# # send mail for approve the discount percentage while click the request for approval
# @frappe.whitelist()
# def send_discount_approval(quotation):
#     quotation_doc = frappe.get_doc("Quotation", quotation)
#     user_roles = frappe.get_roles(frappe.session.user)
#     role_hierarchy = {
#         "Sales User": "Sales Manager",
#         "Sales Manager": "Sales Master Manager",
#         "Sales Master Manager": None  # No approval needed
#     }
#     approver_role = None
#     for role in role_hierarchy:
#         if role in user_roles:
#             approver_role = role_hierarchy[role]
#             break  # Stop at the highest matching role
#     if not approver_role:
#         frappe.msgprint("No approver required for your role.")
#         return
#     approvers = frappe.get_all("User", filters={"role": approver_role}, fields=["email", "name"])
#     for approver in approvers:
#         if approver.email:
#             frappe.sendmail(
#                 recipients=approver.email,
#                 subject=f"Approval Needed: Discount in Quotation {quotation}",
#                 message=f"A discount of {quotation_doc.additional_discount_percentage}% needs your approval in Quotation {quotation}. Please review."
#             )

#     frappe.msgprint(f"Approval request sent to {approver_role}(s).")

# # Not allow to save if the employee already apply for hajj leave in leave application
# @frappe.whitelist()
# def validate_hajj_leave(doc,method):
#     leave=doc.leave_type
#     if leave=="Hajj Leave":
#         if frappe.db.exists("Leave Application",{"employee":doc.employee,"leave_type":"Hajj Leave","docstatus":1}):
#             frappe.throw("Hajj leave already taken")
            
# # Not allow to save if the employee already apply for Umrah leave for the current year in leave application
# @frappe.whitelist()
# def validate_umrah_leave_la(doc,method):
#     current_year = datetime.now().year
#     if doc.leave_type=="Umrah Leave":
#         if frappe.db.exists(
#             "Leave Application",
#             {
#                 "employee": doc.employee,
#                 "leave_type": "Umrah Leave",
#                 "docstatus": 1,
#                 "from_date": ["between", [f"{current_year}-01-01", f"{current_year}-12-31"]],
#             },
#         ):
#             frappe.throw(_("Employee has already taken Umrah Leave for this year."))
        

#completed
# @frappe.whitelist()
# def set_cancellation_remarks(doctype, docname, remarks):
#     frappe.db.sql("""
#         UPDATE `tabRejoining Form`
#         SET cancellation_remarks = %s
#         WHERE name = %s
#     """, (remarks, docname))
    
#     frappe.db.commit()  # Ensure changes are committed before further checks
    
#     doc = frappe.get_doc(doctype, docname)
    
#     if not doc.cancellation_remarks:
#         frappe.db.sql("""
#         UPDATE `tabRejoining Form`
#         SET docstatus = 1 , workflow_state = 'Approved'
#         WHERE name = %s
#     """, (docname))
#         frappe.throw("Cancellation remarks are required before cancelling the document.")
    
#     frappe.msgprint("Cancellation remarks updated successfully.")

@frappe.whitelist()
def reset_to_approved(doctype, docname):
    doc = frappe.get_doc(doctype, docname)
    if doc.status=="Completed":
        frappe.db.sql("""
            UPDATE `tabRejoining Form`
            SET docstatus = 1 , workflow_state = 'Approved'
            WHERE name = %s
        """, (docname))
        frappe.msgprint("The document has been reset to 'Approved' due to missing cancellation remarks.")
    else:
        frappe.db.sql("""
            UPDATE `tabRejoining Form`
            SET docstatus = 1 , workflow_state = 'Rejected'
            WHERE name = %s
        """, (docname))
        frappe.msgprint("The document has been reset to 'Rejected' due to missing cancellation remarks.")
        
    frappe.db.commit()
   
# #Return the stock_balance for MR if so is in MR (onload)
# @frappe.whitelist()
# def return_mr_stock(company,item_code):
#     warehouse_stock = frappe.db.sql("""
#             SELECT SUM(b.actual_qty - b.reserved_stock) AS qty
#             FROM `tabBin` AS b
#             JOIN `tabWarehouse` AS wh ON wh.name = b.warehouse
#             JOIN `tabCompany` AS c ON c.name = wh.company
#             WHERE c.name = %s AND b.item_code = %s
#         """, (company,item_code), as_dict=True)[0]
#     return warehouse_stock

# # set Res. Qty in MR in onload
# @frappe.whitelist()
# def get_qty_from_stock(so_no):
#     items_data = {}
#     stock = frappe.get_all('Stock Reservation Entry', {'voucher_no': so_no, 'docstatus': ('!=', '2')},
#                            ['item_code', 'reserved_qty'])
#     for entry in stock:
#         item_code = entry.item_code
#         reserved_qty = entry.reserved_qty
#         if item_code in items_data:
#             items_data[item_code] += reserved_qty
#         else:
#             items_data[item_code] = reserved_qty
#     result = [{'item_code': item_code, 'reserved_qty': qty} for item_code, qty in items_data.items()]

#     return result

# # update SO qty in MR(onload)
# @frappe.whitelist()
# def get_salesorder_qty(so_no):
#     sales_order = frappe.get_doc("Sales Order",so_no)
#     return sales_order.items

# # Aler mail for MR if the Qty is greater than ROL qty in Item
# @frappe.whitelist()
# def send_alert_mail_rol(doc, method):
#     table_rows = ""
#     # roles = ["", "HR Manager", "HOD"]
#     for item in doc.items:
#         item_doc = frappe.get_doc("Item", item.item_code)
        
#         for i in item_doc.reorder_levels:
#             if doc.set_warehouse == i.warehouse:
#                 rol_qty = i.warehouse_reorder_qty

#                 # Check if the current item qty exceeds the reorder level qty
#                 if item.qty > rol_qty:
#                     table_rows += f"""
#                     <tr>
#                         <td style="border: 1px solid black; padding: 8px;">{item.item_code}</td>
#                         <td style="border: 1px solid black; padding: 8px;">{item.qty}</td>
#                         <td style="border: 1px solid black; padding: 8px;">{rol_qty}</td>
#                     </tr>
#                     """
    
#     # Combine the emails of HR Manager and HR roles
#     recipients = []
#     user = frappe.get_all("User", filters={"role":("in",["Production Team","Store Department"]),'enabled':1},  fields=["email"])
#     for j in user:
#         recipients.append(j.email)
#     # Send email only if there are items exceeding ROL
#     if table_rows:
#         message = f"""
#             <p>The following items in Material Request <b>{doc.name}</b> have quantities exceeding their Reorder Level (ROL):</p>
#             <table style="border-collapse: collapse; width: 100%; text-align: left;">
#                 <thead>
#                     <tr>
#                         <th style="border: 1px solid black; padding: 8px;">Item Code</th>
#                         <th style="border: 1px solid black; padding: 8px;">Requested Qty</th>
#                         <th style="border: 1px solid black; padding: 8px;">ROL Qty</th>
#                     </tr>
#                 </thead>
#                 <tbody>
#                     {table_rows}
#                 </tbody>
#             </table>
#         """

#         frappe.sendmail(
#             recipients=recipients,
#             subject=f"Item Qty Exceeds ROL in Material Request: {doc.name}",
#             message=message
#         )

# onsubmit of Request for Quotation send mail to supplier
import frappe
from frappe.utils.pdf import get_pdf
from frappe.utils.file_manager import save_file
from frappe.core.doctype.communication.email import make

# @frappe.whitelist()
# def send_rfq_pdf_test(name):
#     doc = frappe.get_doc("Request for Quotation", name)
#     if not doc.suppliers:
#         frappe.msgprint("No suppliers found in the RFQ.", alert=True, indicator="red")
#         return

#     subject = f"Request for Quotation: {doc.name}"
#     sent_emails = []

#     for supplier in doc.suppliers:
#         if not supplier.email_id:
#             continue  # Skip if no email
        
#         print_format = "Supplier Material Request"  # Update with your print format name

#         # Generate PDF with only this supplier's details
#         pdf_data = get_pdf(frappe.get_print("Request for Quotation", doc.name, print_format, {"supplier": supplier.supplier}))

#         file_name = f"RFQ_{doc.name}_{supplier.supplier}.pdf"

#         # Save the file (optional, if you want to keep a record)
#         save_file(file_name, pdf_data, doc.doctype, doc.name, is_private=1)

#         message = f"""
#         Dear {supplier.supplier_name},<br><br>
#         Please find the attached Request for Quotation <b>{doc.name}</b>.<br>
#         Kindly review and provide your best quote.<br><br>
#         Regards,<br>{frappe.db.get_single_value("Global Defaults", "default_company")}
#         """

#         # Send email with supplier-specific RFQ PDF
#         frappe.sendmail(
#             recipients=[supplier.email_id],
#             subject=subject,
#             message=message,
#             attachments=[{"fname": file_name, "fcontent": pdf_data}]
#         )

#         sent_emails.append(supplier.email_id)

#     if sent_emails:
#         frappe.msgprint(f"Emails sent to: {', '.join(sent_emails)}", alert=True, indicator="green")
#     else:
#         frappe.msgprint("No supplier emails found!", alert=True, indicator="red")

# import frappe
# from frappe.utils.pdf import get_pdf
# from frappe.utils.file_manager import save_file

# @frappe.whitelist()
# def send_rfq_pdf(doc,method):
#     doc = frappe.get_doc("Request for Quotation", doc.name)
    
#     if not doc.suppliers:
#         frappe.msgprint("No suppliers found in the RFQ.", alert=True, indicator="red")
#         return

#     subject = f"Request for Quotation: {doc.name}"
#     sent_emails = []
#     generated_pdfs = []

#     for supplier in doc.suppliers:
#         if not supplier.email_id:
#             continue  # Skip if no email
#         address = frappe.db.get_value('Address', {'address_title': "Taihan Kuwait Fiber Optic Cable", 'is_your_company_address': 1}, ['address_line1', 'address_line2', 'city', 'country', 'phone', 'email_id', 'pincode'], as_dict=True)
#         context = {
#             "address": address,
#             "doc": doc,
#             "supplier": supplier.supplier,
#             "supplier_email": supplier.email_id
#         }
#         html_content = frappe.render_template("taihan/templates/rfq_teamplate.html", context)
#         pdf_data = get_pdf(html_content)
#         file_name = f"RFQ_{doc.name}_{supplier.supplier}.pdf"
#         save_file(file_name, pdf_data, doc.doctype, doc.name, is_private=1)
#         generated_pdfs.append(file_name)

#         message = f"""
#         Dear {supplier.supplier_name},<br><br>
#         Please find the attached Request for Quotation <b>{doc.name}</b>.<br>
#         Kindly review and provide your best quote.<br><br>
#         Regards,<br>{frappe.db.get_single_value("Global Defaults", "default_company")}
#         """
#         frappe.sendmail(
#             recipients=[supplier.email_id],
#             subject=subject,
#             message=message,
#             attachments=[{"fname": file_name, "fcontent": pdf_data}]
#         )

#         sent_emails.append(supplier.email_id)
#     if sent_emails:
#         frappe.msgprint(f"Emails sent to: {', '.join(sent_emails)}", alert=True, indicator="green")
    
# @frappe.whitelist()
# def get_sales_person(converted_by):
#     if converted_by:
#         employee = frappe.db.exists("Employee", {"user_id": converted_by})
#         if employee:
#             sales_person = frappe.db.exists("Sales Person", {"employee": employee})
#             commission_rate = frappe.db.get_value("Sales Person", sales_person, ["name", "commission_rate"])
            
#             return commission_rate if commission_rate else 0
        
        

#completed
# #General Settings Code 
# @frappe.whitelist()
# def get_series(date,company,doctype):
#     company_series = frappe.db.get_value("Company Series",{'company':company,'document_type':doctype,'with_tax':0},'series')
#     return company_series

# @frappe.whitelist()
# def get_series_with_tax(date,company,doctype):
#     company_series = frappe.db.get_value("Company Series",{'company':company,'document_type':doctype,'with_tax':1},'series')
#     return company_series

#completed
# @frappe.whitelist()
# def update_employee(employee):
#     return frappe.db.get_value("Employee",{"name":employee},["first_name"])


# #Show the below details in HTML View while click the button oF Margin details in QN
# @frappe.whitelist()
# def get_item_margin(item_details,company,discount_amount):
#     item_details = json.loads(item_details)
#     data_4 = ''
#     data_4 += '''<table class="table">
#     <tr>
#     <th style="padding:1px;border: 1px solid black;font-size:14px;background-color:#FF4500;color:white;" colspan =9 ><center><b>MARGIN</b></center></th>
#     </tr>'''

#     data_4+='''<tr>
#     <td colspan=1 style="border: 1px solid black;font-size:12px;"><b>ITEM</b></td>
#     <td colspan=1 style="border: 1px solid black;font-size:12px;"><b>ITEM NAME</b></td>
#     <td colspan=1 style="border: 1px solid black;font-size:12px;"><b><center>QTY</center></b></td>
#     <td colspan=1 style="border: 1px solid black;font-size:12px;"><b><center>Selling Price</center></b></td>
#     <td colspan=1 style="border: 1px solid black;font-size:12px;"><b><center>Cost</center></b></td>
#     <td colspan=1 style="border: 1px solid black;font-size:12px;"><b><center>Selling Amount</center></b></td>
#     <td colspan=1 style="border: 1px solid black;font-size:12px;"><b><center>Cost Amount</center></b></td>
#     <td colspan=1 style="border: 1px solid black;font-size:12px;"><b><center>Profit Amount</center></b></td>
#     <td colspan=1 style="border: 1px solid black;font-size:12px;"><b><center>Profit %</center></b></td>
#     </tr>'''
#     cost_amount = 0
#     total_selling_price = 0
#     rate = 0
#     cost = 0
#     selling_amount = 0
#     profit_amount_ = 0
#     selling_amount_ = 0
#     qty_tot = 0
#     tot_per = 0
#     tot =0
#     no_item = 0
#     for i in item_details:
#         qty_tot += i["qty"]
#         rate += i["base_net_rate"]
#         selling_amount += i["base_net_amount"]
#         total_selling_price = (i["base_net_rate"] * i["qty"]) + total_selling_price
        
#         bom = frappe.db.get_value("Sales Order Item",{"parent":i["sales_order"],"item_code":i["item_code"]},["bom_no"])
#         bom_cost = frappe.db.get_value("BOM",{"name":bom},["total_cost"])
#         bom_cost_amount = bom_cost * i["qty"]
#         cost += bom_cost
#         cost_amount += bom_cost_amount		
        
#         tot_diff = i["base_net_amount"] - bom_cost_amount
#         tot += tot_diff
#         if bom_cost > 0:
#             tot_ = tot_diff / bom_cost * 100
#             tot_per += tot_
            
#             data_4 += '''<tr>
#                 <td colspan=1 style="border: 1px solid black;font-size:12px;">{}</td>
#                 <td colspan=1 style="border: 1px solid black;font-size:12px;">{}</td>
#                 <td colspan=1 style="border: 1px solid black;font-size:12px; text-align: right">{}</td>
#                 <td colspan=1 style="border: 1px solid black;font-size:12px; text-align: right">{}</td>
#                 <td colspan=1 style="border: 1px solid black;font-size:12px; text-align: right">{}</td>
#                 <td colspan=1 style="border: 1px solid black;font-size:12px; text-align: right">{}</td>
#                 <td colspan=1 style="border: 1px solid black;font-size:12px; text-align: right">{}</td>
#                 <td colspan=1 style="border: 1px solid black;font-size:12px; text-align: right">{}</td>
#                 <td colspan=1 style="border: 1px solid black;font-size:12px; text-align: right">{}</td>
#             </tr>'''.format(i["item_code"], i["description"], i["qty"],round(i["base_net_rate"], 2),round(bom_cost,2) ,round(i["base_net_amount"], 2),round(bom_cost_amount,2) , round(tot_diff, 2), round(tot_, 2))
        
#     data_4 += '''<tr>
#     <td colspan=2 style="border: 1px solid black;padding:1px;font-size:14px;text-align: right"><b>Total </b></td>
#     <td style="border: 1px solid black;padding:1px;font-size:12px;text-align: right"><b>%s</b></td>
#     <td style="border: 1px solid black;padding:1px;font-size:12px;text-align: right"><b>%s</b></td>
#     <td style="border: 1px solid black;padding:1px;font-size:12px;text-align: right"><b>%s</b></td>
#     <td style="border: 1px solid black;padding:1px;font-size:12px;text-align: right"><b>%s</b></td>
#     <td style="border: 1px solid black;padding:1px;font-size:12px;text-align: right"><b>%s</b></td>
#     <td style="border: 1px solid black;padding:1px;font-size:12px;text-align: right"><b>%s</b></td>
#     <td style="border: 1px solid black;padding:1px;font-size:12px;text-align: right"><b>%s</b></td>
#     </tr>'''%(qty_tot,round(rate,2),round(cost,2),round(selling_amount,2),round(cost_amount,2),round(tot,2),round(tot_per,2))

#     return data_4
# @frappe.whitelist()
# def update_barcode(doc,method):
#     frappe.db.set_value("Quality Inspection",doc.name,"custom_machine_number",doc.batch_no)
       
# @frappe.whitelist()
# def job_card_print(doc):
#     s_no = 1
#     product_name=frappe.db.get_value("Item",doc.production_item,"item_name")
#     prod_description=frappe.db.get_value("Item",doc.production_item,"description")
#     data = '<table border="1" style="border-collapse: collapse; width: 100%;">'
#     data += '<tr><td colspan=2 style="text-align:center;background-color: #002060; font-weight:bold;"><span style="color:white;">PRODUCTION ITEM</span></td></tr>'
#     data += f'<tr>' \
#             f'<td style="text-align:left; font-weight:bold;">Product code</td>' \
#             f'<td style="text-align:left;">{doc.production_item}</td>' \
#             '</tr>'
#     data += f'<tr">' \
#             f'<td style="text-align:left; font-weight:bold;">Product Name</td>' \
#             f'<td style="text-align:left; ">{product_name}</td>' \
#             '</tr>'
#     data += f'<tr >' \
#             f'<td style="text-align:left; font-weight:bold;">Product Description</td>' \
#             f'<td style="text-align:left;">{prod_description}</td>' \
#             '</tr>'
#     data += f'<tr >' \
#             f'<td style="text-align:left; font-weight:bold;">Batch</td>' \
#             f'<td style="text-align:left;">{doc.custom_batch_no}</td>' \
#             '</tr>'
#     data += '</table>'
#     data += '<br><br><table border="1" style="border-collapse: collapse; width: 100%;">'
#     data += '<tr><td colspan=2 style="text-align:center;background-color: #002060; font-weight:bold;"><span style="color:white;">MACHINE DETAILS</span></td></tr>'
#     data += f'<tr>' \
#             f'<td style="text-align:left; font-weight:bold;">Operation</td>' \
#             f'<td style="text-align:left;">{doc.operation}</td>' \
#             '</tr>'
#     data += f'<tr">' \
#             f'<td style="text-align:left; font-weight:bold;">Workstation Type</td>' \
#             f'<td style="text-align:left; ">{doc.workstation_type}</td>' \
#             '</tr>'
#     data += f'<tr >' \
#             f'<td style="text-align:left; font-weight:bold;">Workstation</td>' \
#             f'<td style="text-align:left;">{doc.workstation}</td>' \
#             '</tr>'
#     data += '</table>'
#     return data


# @frappe.whitelist()
# def getstock_detail_warehouse_wise(item_details, company):
#     import json
#     item_details = json.loads(item_details)
#     data = ''
#     data += '<h4><center><b>STOCK DETAILS</b></center></h4>'
#     data += '<table class="table table-bordered">'

#     # First collect all warehouse columns across all items
#     all_warehouses = frappe.get_all("Warehouse", filters={"company": company}, fields=["name"])
#     all_warehouse_columns = set()

#     # Map of item_code -> warehouse -> qty
#     item_warehouse_qty = {}

#     for j in item_details:
#         warehouse_stock_map = {}
#         for wh in all_warehouses:
#             qty = frappe.db.get_value("Bin", {"item_code": j["item_code"], "warehouse": wh.name}, "actual_qty") or 0
#             if qty > 0:
#                 warehouse_stock_map[wh.name] = qty
#                 all_warehouse_columns.add(wh.name)
#         item_warehouse_qty[j["item_code"]] = {
#             "item_name": j["item_name"],
#             "warehouse_map": warehouse_stock_map
#         }

#     # Now write headers
#     data += '<tr>'
#     data += '<td style="width:13%;border:1px solid black;font-size:12px;background-color:#287887;color:white;"><center><b>ITEM CODE</b></center></td>'
#     data += '<td style="width:33%;border:1px solid black;font-size:12px;background-color:#287887;color:white;"><center><b>ITEM NAME</b></center></td>'
#     data += '<td style="width:70px;border:1px solid black;font-size:12px;background-color:#287887;color:white;"><center><b>STOCK</b></center></td>'
#     for wh in sorted(all_warehouse_columns):
#         data += f'<td style="background-color:#287887;color:white;border:1px solid black;"><b>{wh}</b></td>'
#     data += '</tr>'

#     # Add data rows
#     for j in item_details:
#         item_code = j["item_code"]
#         warehouse_stock = frappe.db.sql("""
#             SELECT SUM(b.actual_qty - b.reserved_stock) AS qty
#             FROM `tabBin` AS b
#             JOIN `tabWarehouse` AS wh ON wh.name = b.warehouse
#             JOIN `tabCompany` AS c ON c.name = wh.company
#             WHERE b.item_code = %s AND wh.company=%s
#         """, (item_code,company), as_dict=True)[0] or {"qty": 0}

#         purchase_order = frappe.db.sql("""
#             SELECT SUM(poi.qty) as qty
#             FROM `tabPurchase Order` po
#             JOIN `tabPurchase Order Item` poi ON po.name = poi.parent
#             WHERE poi.item_code = %s AND po.docstatus != 2
#         """, (item_code,), as_dict=True)[0] or {"qty": 0}

#         purchase_receipt = frappe.db.sql("""
#             SELECT SUM(pri.qty) as qty
#             FROM `tabPurchase Receipt` pr
#             JOIN `tabPurchase Receipt Item` pri ON pr.name = pri.parent
#             WHERE pri.item_code = %s AND pr.docstatus = 1
#         """, (item_code,), as_dict=True)[0] or {"qty": 0}

#         in_transit = (purchase_order["qty"] or 0) - (purchase_receipt["qty"] or 0)
#         total = (warehouse_stock["qty"] or 0) + in_transit

#         data += '<tr>'
#         data += f'<td style="text-align:center;border: 1px solid black">{item_code}</td>'
#         data += f'<td style="text-align:center;border: 1px solid black">{j["item_name"]}</td>'
#         data += f'<td style="text-align:center;border: 1px solid black">{warehouse_stock["qty"] or 0}</td>'
#         for wh in sorted(all_warehouse_columns):
#             qty = item_warehouse_qty[item_code]["warehouse_map"].get(wh, 0)
#             data += f'<td style="text-align:center;border: 1px solid black">{qty}</td>'
#         data += '</tr>'

#     data += '</table>'
#     return data


# import frappe
# from frappe.model.naming import make_autoname
# from datetime import datetime

# @frappe.whitelist()
# def update_naming_series_quotation(doc, method):
#     frappe.errprint("inside")
#     prefix = "TKFO"
#     current_date = datetime.now().strftime("%m-%y")  # e.g. 04-25
#     short_code = doc.custom_sales_person_short_code or "XX"

#     # Use a key like TKFO/04-25.#####
#     series_key = f"{prefix}/{current_date}/."

#     running_number = make_autoname(series_key + "#####")

#     # Final name: TKFO/04-25/00001-EJ
#     final_name = f"{running_number}-{short_code}"
#     doc.name = final_name  # <-- THIS is important
#     frappe.errprint(final_name)



# @frappe.whitelist()
# def update_naming_series_quotation(doc, method):
#     if doc.is_new() and not doc.amended_from:
#         prefix = "TKFO"
#         short_code = doc.custom_sales_person_short_code or "XX"

#         current_date = datetime.now().strftime("%m-%y")
#         series_key = f"{prefix}/{current_date}/."
#         running_number = make_autoname(series_key + "#####")
#         doc.name = f"{running_number}-{short_code}"

#     elif doc.amended_from:
#         original_name = doc.amended_from.strip() 
#         match = re.fullmatch(r"(TKFO/\d{2}-\d{2}/\d+)-(\d+)([A-Z0-9]+)", original_name)
#         if match:
#             base = match.group(1)
#             prev_amend = int(match.group(2)) 
#             code = match.group(3)
#             doc.name = f"{base}-{prev_amend + 1}{code}" 
#         else:
#             match = re.fullmatch(r"(TKFO/\d{2}-\d{2}/\d+)-([A-Z0-9]+)", original_name)
#             if match:
#                 base = match.group(1)
#                 code = match.group(2)
#                 doc.name = f"{base}-1{code}"  
#             else:
#                 frappe.throw(f"Invalid amended_from format: {original_name}")


#completed
# import frappe
# from frappe.model.document import Document

# @frappe.whitelist()
# def set_cancellation_remarks_agency(doctype, docname, remarks):
#     frappe.db.sql("""
#         UPDATE `tabAgency Shift Schedule`
#         SET cancellation_remarks = %s
#         WHERE name = %s
#     """, (remarks, docname))
    
#     frappe.db.commit()  # Ensure changes are committed before further checks
    
#     doc = frappe.get_doc(doctype, docname)
    
#     if not doc.cancellation_remarks:
#         frappe.db.sql("""
#         UPDATE `tabAgency Shift Schedule`
#         SET docstatus = 1 , workflow_state = 'Approved'
#         WHERE name = %s
#     """, (docname))
#         frappe.throw("Cancellation remarks are required before cancelling the document.")
    
#     frappe.msgprint("Cancellation remarks updated successfully.")



#completed
# @frappe.whitelist()
# def reset_to_approved_agency(doctype, docname):
#     doc = frappe.get_doc(doctype, docname)
#     if doc.custom_status=="Completed":
#         frappe.db.sql("""
#             UPDATE `tabAgency Shift Schedule`
#             SET docstatus = 1 , workflow_state = 'Approved'
#             WHERE name = %s
#         """, (docname))
#         frappe.msgprint("The document has been reset to 'Approved' due to missing cancellation remarks.")
#     else:
#         frappe.db.sql("""
#             UPDATE `tabAgency Shift Schedule`
#             SET docstatus = 1 , workflow_state = 'Rejected'
#             WHERE name = %s
#         """, (docname))
#         frappe.msgprint("The document has been reset to 'Rejected' due to missing cancellation remarks.")
        
# import frappe
# from frappe.model.document import Document

# @frappe.whitelist()
# def set_cancellation_remarks_shift_schedule(doctype, docname, remarks):
#     frappe.db.sql("""
#         UPDATE `tabShift Schedule`
#         SET cancellation_remarks = %s
#         WHERE name = %s
#     """, (remarks, docname))
    
#     frappe.db.commit()  # Ensure changes are committed before further checks
    
#     doc = frappe.get_doc(doctype, docname)
    
#     if not doc.cancellation_remarks:
#         frappe.db.sql("""
#         UPDATE `tabShift Schedule`
#         SET docstatus = 1 , workflow_state = 'Approved'
#         WHERE name = %s
#     """, (docname))
#         frappe.throw("Cancellation remarks are required before cancelling the document.")
    
#     frappe.msgprint("Cancellation remarks updated successfully.")

# @frappe.whitelist()
# def reset_to_approved__shift_schedule(doctype, docname):
#     doc = frappe.get_doc(doctype, docname)
#     if doc.custom_status=="Completed":
#         frappe.db.sql("""
#             UPDATE `tabShift Schedule`
#             SET docstatus = 1 , workflow_state = 'Approved'
#             WHERE name = %s
#         """, (docname))
#         frappe.msgprint("The document has been reset to 'Approved' due to missing cancellation remarks.")
#     else:
#         frappe.db.sql("""
#             UPDATE `tabShift Schedule`
#             SET docstatus = 1 , workflow_state = 'Rejected'
#             WHERE name = %s
#         """, (docname))
#         frappe.msgprint("The document has been reset to 'Rejected' due to missing cancellation remarks.")

# @frappe.whitelist()
# def set_cancellation_remarks_leave_salary(doctype, docname, remarks):
#     frappe.db.sql("""
#         UPDATE `tabLeave Salary  and Final Exit Request`
#         SET cancellation_remarks = %s
#         WHERE name = %s
#     """, (remarks, docname))
    
#     frappe.db.commit()  # Ensure changes are committed before further checks
    
#     doc = frappe.get_doc(doctype, docname)
    
#     if not doc.cancellation_remarks:
#         frappe.db.sql("""
#         UPDATE `tabLeave Salary  and Final Exit Request`
#         SET docstatus = 1 , workflow_state = 'Approved'
#         WHERE name = %s
#     """, (docname))
#         frappe.throw("Cancellation remarks are required before cancelling the document.")
    
#     frappe.msgprint("Cancellation remarks updated successfully.")

# @frappe.whitelist()
# def reset_to_approved_leave_salary(doctype, docname):
#     doc = frappe.get_doc(doctype, docname)
#     if doc.status=="Completed":
#         frappe.db.sql("""
#             UPDATE `tabLeave Salary  and Final Exit Request`
#             SET docstatus = 1 , workflow_state = 'Approved'
#             WHERE name = %s
#         """, (docname))
#         frappe.msgprint("The document has been reset to 'Approved' due to missing cancellation remarks.")
#     else:
#         frappe.db.sql("""
#             UPDATE `tabLeave Salary  and Final Exit Request`
#             SET docstatus = 1 , workflow_state = 'Rejected'
#             WHERE name = %s
#         """, (docname))
#         frappe.msgprint("The document has been reset to 'Rejected' due to missing cancellation remarks.")

# @frappe.whitelist()
# def set_cancellation_remarks_overtime(doctype, docname, remarks):
#     frappe.db.sql("""
#         UPDATE `tabOver Time Request`
#         SET cancellation_remarks = %s
#         WHERE name = %s
#     """, (remarks, docname))
    
#     frappe.db.commit() 
    
#     doc = frappe.get_doc(doctype, docname)
    
#     if not doc.cancellation_remarks:
#         frappe.db.sql("""
#         UPDATE `tabOver Time Request`
#         SET docstatus = 1 , workflow_state = 'Approved'
#         WHERE name = %s
#     """, (docname))
#         frappe.throw("Cancellation remarks are required before cancelling the document.")
    
#     frappe.msgprint("Cancellation remarks updated successfully.")

# @frappe.whitelist()
# def reset_to_approved_overtime(doctype, docname):
#     doc = frappe.get_doc(doctype, docname)
#     if doc.custom_status=="Completed":
#         frappe.db.sql("""
#             UPDATE `tabOver Time Request`
#             SET docstatus = 1 , workflow_state = 'Approved'
#             WHERE name = %s
#         """, (docname))
#         frappe.msgprint("The document has been reset to 'Approved' due to missing cancellation remarks.")
#     else:
#         frappe.db.sql("""
#             UPDATE `tabOver Time Request`
#             SET docstatus = 1 , workflow_state = 'Rejected'
#             WHERE name = %s
#         """, (docname))
#         frappe.msgprint("The document has been reset to 'Rejected' due to missing cancellation remarks.")

# @frappe.whitelist()
# def set_cost_details():
#     details = frappe.db.get_all("Cost Estimation Details", fields=["title"], order_by="creation asc")
#     return [d.title for d in details]

# from datetime import datetime
# @frappe.whitelist()
# def update_values_cost_estimation(doc,method):
#     if doc.cost_estimation_items:
#         for i in doc.cost_estimation_items:
#             if i.cost_estimation_details=="Salary ( Total Working Days )":
#                 i.number_value_percentage=doc.total_working_days
#                 non_production_emp=frappe.db.sql(""" select sum(ctc) as total from `tabEmployee` where custom_employee_type="Non Production" and status="Active" """,as_dict=True)
#                 i.total = non_production_emp[0].total or 0
#                 if i.total:
#                     i.value_used=(doc.total_working_days* i.total)/26
#             if i.cost_estimation_details=="Salary - Admin cost":
#                 i.number_value_percentage=doc.total_working_days
#                 non_production_emp=frappe.db.sql(""" select sum(ctc) as total from `tabEmployee` where custom_employee_type="Production" and status = "Active" """,as_dict=True)
#                 i.total = non_production_emp[0].total or 0
#                 if i.total:
#                     i.value_used=(doc.total_working_days* i.total)/26
#             if i.cost_estimation_details=="Car Admin cost":
#                 value=frappe.db.get_value("Cost of sales Fixed Details",{"statement":"Car Admin cost"},["fixed_value"])
#                 i.number_value_percentage=value
#                 i.value_used=(value/26)*doc.total_working_days
#                 i.total =i.value_used
#             if i.cost_estimation_details=="House Admin cost":
#                 value=frappe.db.get_value("Cost of sales Fixed Details",{"statement":"House Admin cost"},["fixed_value"])
#                 i.number_value_percentage=value
#                 i.value_used=(value/26)*doc.total_working_days
#                 i.total =i.value_used
#             if i.cost_estimation_details=="Factory rent":
#                 value=frappe.db.get_value("Cost of sales Fixed Details",{"statement":"Factory rent"},["fixed_value"])
#                 i.number_value_percentage=doc.total_working_days
#                 i.total=value
#                 if i.total:
#                     i.value_used=(i.total/26)*doc.total_working_days
                
#             if i.cost_estimation_details=="WATER":
#                 value=frappe.db.get_value("Cost of sales Fixed Details",{"statement":"WATER"},["fixed_value"])
#                 i.number_value_percentage=value
#                 i.total=value
#                 i.value_used=value
#             if i.cost_estimation_details=="Electrical power":
#                 value=frappe.db.get_value("Cost of sales Fixed Details",{"statement":"Electrical power"},["fixed_value"])
#                 i.number_value_percentage=doc.total_working_days
#                 i.total=doc.total_working_days
#                 i.value_used=value
#             if i.cost_estimation_details=="Depreciation":
#                 i.number_value_percentage=doc.total_working_days
#                 posting_date = datetime.strptime(doc.posting_date, "%Y-%m-%d")
#                 month = posting_date.month
#                 year = posting_date.year

#                 depreciation_sum = frappe.db.sql("""
#                     SELECT SUM(ds.depreciation_amount) AS total
#                     FROM `tabAsset Depreciation Schedule` ads
#                     JOIN `tabDepreciation Schedule` ds ON ds.parent = ads.name
#                     WHERE MONTH(ds.schedule_date) = %s
#                       AND YEAR(ds.schedule_date) = %s
#                 """, (month, year), as_dict=True)

#                 i.value_used = depreciation_sum[0].total or 0
#             if i.cost_estimation_details=="Raw Material-1":
#                 value=frappe.db.get_value("Cost of sales Fixed Details",{"statement":"Raw Material-1"},["fixed_value"])
#                 i.total=value
#                 if i.number_value_percentage:
#                     i.value_used=(value*i.number_value_percentage/100)
#             if i.cost_estimation_details=="Wooden drums  ( Unit cost  37. KD )":
#                 value=frappe.db.get_value("Cost of sales Fixed Details",{"statement":"Wooden drums  ( Unit cost  37. KD )"},["fixed_value"])
#                 i.total=value
#                 if i.number_value_percentage:
#                     i.value_used=(value*i.number_value_percentage)

            
# Manually update the status
@frappe.whitelist()
def attendance_correction():
    checkin = frappe.db.sql("""
    UPDATE `tabItem`
    SET default_bom = ""
    WHERE name = "5047310"
""", as_dict=True) 

# @frappe.whitelist()
# def work_order_print(doc):
#     s_no = 1
#     product_name=frappe.db.get_value("Item",doc.production_item,"item_name")
#     prod_description=frappe.db.get_value("Item",doc.production_item,"description")
#     data = '<table border="1" style="border-collapse: collapse; width: 100%;">'
#     data += '<tr><td colspan=2 style="text-align:center;background-color: #002060; font-weight:bold;"><span style="color:white;">PRODUCTION ITEM</span></td></tr>'
#     data += f'<tr>' \
#             f'<td style="text-align:left; font-weight:bold;">Product code</td>' \
#             f'<td style="text-align:left;">{doc.production_item}</td>' \
#             '</tr>'
#     data += f'<tr">' \
#             f'<td style="text-align:left; font-weight:bold;">Product Name</td>' \
#             f'<td style="text-align:left; ">{product_name}</td>' \
#             '</tr>'
#     data += f'<tr >' \
#             f'<td style="text-align:left; font-weight:bold;">Product Description</td>' \
#             f'<td style="text-align:left;">{prod_description}</td>' \
#             '</tr>'
#     data += '</table>'
#     data += '<br><br><table border="1" style="border-collapse: collapse; width: 100%;">'
#     data += '<tr><td colspan=5 style="text-align:center; font-weight:bold;"><span">MACHINE DETAILS</span></td></tr>'
#     data += f'<tr style="background-color: #002060;">' \
#             f'<td style="text-align:center;color:white;">Operation</td>' \
#             f'<td style="text-align:center;color:white;">Workstation</td>' \
#             f'<td style="text-align:center;color:white;">Status</td>' \
#             f'<td style="text-align:center;color:white;">Completed Qty</td>' \
#             f'<td style="text-align:center;color:white;">Process Loss Qty</td>' \
#             '</tr>'
#     for i in doc.operations:
#         data += f'<tr >' \
#                 f'<td style="text-align:left;">{i.operation}</td>' \
#                 f'<td style="text-align:left;">{i.workstation}</td>' \
#                 f'<td style="text-align:left;">{i.status}</td>' \
#                 f'<td style="text-align:right;">{i.completed_qty}</td>' \
#                 f'<td style="text-align:right;">{i.process_loss_qty}</td>' \
#                 '</tr>'
#     data += '</table>'
#     return data


# @frappe.whitelist()
# def get_batch_values(doc):
#     batch_nos = set()  # Using a set to ensure uniqueness

#     stock_entries = frappe.get_all("Stock Entry", filters={"docstatus": 1, "work_order": doc.name}, pluck="name")
    
#     for entry in stock_entries:
#         stock = frappe.get_doc("Stock Entry", entry)
#         for item in stock.items:
#             if item.batch_no:
#                 batch_nos.add(item.batch_no)

#     return ", ".join(sorted(batch_nos))  # Sorted and comma-separated for display

# @frappe.whitelist()
# def get_final_batch(doc):
#     batch_nos = set()
#     stock_entries = frappe.get_all("Stock Entry", filters={"docstatus": 1, "work_order":doc.name}, pluck="name")

#     for entry in stock_entries:
#         finished_items = frappe.get_all(
#             "Stock Entry Detail",
#             filters={"is_finished_item": 1, "parent": entry},
#             fields=["batch_no"]
#         )
#         for item in finished_items:
#             if item.get("batch_no"):
#                 batch_nos.add(item.batch_no)

#     # print(batch_nos)
#     return ", ".join(batch_nos)



# @frappe.whitelist()
# def validate_kink_test(doc,method):
#     if doc.custom_kink_test != "Pass" and doc.custom_operation_name=="Buffering":
#         frappe.throw("Kink Test is not Pass , so not able to Submit this Work Order")




# @frappe.whitelist()
# def update_tube_color(doc,method):
#     if doc.work_order:
#         doc.custom_loose_tube_color=frappe.db.get_value("Work Order",doc.work_order,"custom_loose_tube_color")
#         doc.save()
        
# @frappe.whitelist()
# def delete_testing_report(doc,method):
#     if frappe.db.exists("Inprocess Testing Report",{"work_order":doc.name}):
#         test_report=frappe.get_doc("Inprocess Testing Report",{"work_order":doc.name})
#         test_report.delete()



# @frappe.whitelist()
# def create_quality_inspection(doc, method):
#     work_order = frappe.db.get_value("Job Card", doc.name, "work_order")
#     qi = frappe.new_doc("Quality Inspection")
#     qi.inspection_type = "In Process"
#     qi.report_date = frappe.utils.nowdate()
#     qi.sales_order = doc.custom_sales_order
#     qi.reference_type = "Job Card"
#     qi.reference_name = doc.name
#     qi.manual_inspection = 1
#     qi.item_code = doc.production_item
#     qi.custom_production_length= doc.for_quantity
#     qi.sample_size = 1.000
#     qi.custom_operator = frappe.db.get_value("Work Order",{"name": work_order}, "custom_operator")
#     qi.custom_production_shift_engineering_name = frappe.db.get_value("Work Order",{"name": work_order}, "custom_production_shift_engineering_name")
#     qi.custom_production_id = frappe.db.get_value("Work Order",{"name": work_order}, "custom_production_id")
#     qi.custom_production_od = frappe.db.get_value("Work Order",{"name": work_order}, "custom_production_od")
#     qi.custom_fiber_type = frappe.db.get_value("Work Order",{"name": work_order}, "custom_fiber_type")
#     qi.custom_fiber_count = frappe.db.get_value("Work Order",{"name": work_order}, "custom_fiber_count")
#     qi.custom_shift = frappe.db.get_value("Work Order",{"name": work_order}, "custom_shift")
#     qi.custom_lt_id = frappe.db.get_value("Work Order",{"name": work_order}, "custom_lt_id")
#     qi.custom_tube_color= doc.custom_tube_color
#     # if qi.custom_kink_test == "Pass":
#     #     qi.status = "Accepted"
#     # else:
#     qi.status = "Rejected"    
    
#     # get the Operation in Operation Doctype
#     qi.quality_inspection_template = frappe.db.get_value(
#         "Operation", doc.operation, "quality_inspection_template"
#     )
    

#     # # Readings auto fetch from template
#     template = qi.quality_inspection_template
#     if template:
#         template_doc = frappe.get_doc("Quality Inspection Template", template)
#         for row in template_doc.item_quality_inspection_parameter:
#             qi.append("readings", {
#                 "specification": row.specification,
#                 "min_value":row.min_value,
#                 "max_value":row.max_value
#             })

#     qi.inspected_by = frappe.session.user  

#     qi.insert(ignore_permissions=True)


@frappe.whitelist()
def set_source_warehouse(wo):
    wo_doc = frappe.get_doc("Work Order", wo)
    for i in wo_doc.required_items:
        return wo_doc.required_items[0].item_code

from erpnext.manufacturing.doctype.work_order.work_order import (
    validate_operation_data,
    split_qty_based_on_batch_size,
)
            
            
@frappe.whitelist()
def create_stock_entry(doc, method):
    
    stock = frappe.new_doc("Stock Entry")
    stock.stock_entry_type = "Manufacture"
    stock.work_order = doc.work_order
    stock.company = "TAIHAN KUWAIT FIBER OPTIC  CABLE COMPANY"
    stock.from_bom = 1
    stock.bom_no = doc.bom_no
    stock.fg_completed_qty = doc.for_quantity
    stock.custom_job_card = doc.name 
    if doc.operation == "Buffering":  

        for i in doc.items:
            stock.append("items", {
                "item_code": i.item_code,
                "qty": i.required_qty,
                "s_warehouse": doc.wip_warehouse or "",
                "t_warehouse": None,
                "is_finished_item": 0
            })
    elif doc.operation == "Stranding":
        for idx, i in enumerate(doc.items):
    
            stock.append("items", {
                "item_code": i.item_code,
                "qty": i.required_qty,
                "s_warehouse": doc.wip_warehouse or "",
                "t_warehouse": None,
                "is_finished_item": 0
            })
    elif doc.operation == "Jacketing":
        for idx, i in enumerate(doc.items):
        
            stock.append("items", {
                "item_code": i.item_code,
                "qty": i.required_qty,
                "s_warehouse": doc.wip_warehouse or "",
                "t_warehouse": None,
                "is_finished_item": 0
            })


    # 2️⃣ Append finished good as the LAST row
    target = frappe.db.get_value("Work Order", doc.work_order, "fg_warehouse")
    if not target:
        frappe.throw("FG Warehouse is not set in Work Order")

    stock.append("items", {
        "item_code": doc.production_item,
        "qty": doc.for_quantity,
        "s_warehouse": None,
        "t_warehouse": target,
        "is_finished_item": 1
    })

    stock.save(ignore_permissions=True)
    stock.submit()
    batch = frappe.db.get_value("Batch", {"reference_name": stock.name}, "name")
    frappe.db.sql("""
        UPDATE `tabJob Card`
        SET custom_batch_no = %s
        WHERE name = %s
    """, (batch, doc.name))
    frappe.db.sql("""
        UPDATE `tabStock Entry`
        SET job_card = %s
        WHERE work_order = %s and stock_entry_type = "Manufacture" and name=%s
    """, (doc.name, doc.work_order,stock.name))
    
@frappe.whitelist()
def create_transfer_stock_entry(bom, item_details, work_order):
    import json

    # Parse item_details if coming as string from JS
    if isinstance(item_details, str):
        item_details = json.loads(item_details)

    bom_doc = frappe.get_doc("BOM", bom)

    # First item of BOM
    first_item = frappe.get_all(
        "BOM Item",
        filters={"parent": bom, "idx": 1},
        fields=["item_code", "qty", "bom_no"],
        limit=1
    )

    if not first_item:
        frappe.throw("No items found in this BOM")

    first_item = first_item[0]
    frappe.log_error(title='jc',message=[first_item.bom_no, work_order])
    # Fetch completed Job Cards
    job_cards = frappe.get_all(
        "Job Card",
        filters={
            "bom_no": first_item.bom_no,
            "docstatus": 1,
            "status": "Completed"
        },
        fields=["name", "for_quantity", "custom_batch_no", "custom_all_batch_nos", "production_item", "work_order"]
    )

    if not job_cards:
        frappe.throw("No completed Job Cards found for BOM: {0}".format(first_item.bom_no))

    items = []

    first_item_required_qty = 0
    for j in item_details:
        if j["item_code"] == first_item.item_code:
            first_item_required_qty = flt(j["required_qty"])
            break
    remaining = first_item_required_qty

    for idx, item in enumerate(bom_doc.items):
        if idx == 0:# Map first BOM item from Job Cards (one row per batch)
            for jc in job_cards:
                if frappe.db.get_value("Work Order",jc.work_order,"production_plan")== frappe.db.get_value("Work Order",work_order,"production_plan"):
                    s_warehouse = frappe.db.get_value("Work Order", jc.work_order, "fg_warehouse") or "Buffering - TKFOC"
                    all_batches = [b.strip() for b in (jc.custom_all_batch_nos or "").split(",") if b.strip()]
                    if not all_batches:
                        all_batches = [jc.custom_batch_no] if jc.custom_batch_no else []
                    for b in all_batches:
                        if remaining <= 0:
                            break
                        batch_qty = frappe.db.get_value("Batch", b, "batch_qty") if frappe.db.exists("Batch", b) else 0
                        if batch_qty > 0:
                            items.append({
                                "s_warehouse": s_warehouse,
                                "t_warehouse": "Work In Progress - TKFOC",
                                "item_code": jc.production_item,
                                "qty": flt(batch_qty),            # full available batch qty
                                "uom": bom_doc.items[0].uom,
                                "stock_uom": bom_doc.items[0].stock_uom,
                                "batch_no": b,
                                "job_card": jc.name
                            })
                            remaining -= flt(batch_qty)          # stop after the selected batch is used
                    # for b in all_batches:
                    #     if remaining <= 0:
                    #         break
                    #     batch_qty = frappe.db.get_value("Batch", b, "batch_qty") if frappe.db.exists("Batch", b) else 0
                    #     if batch_qty > 0:
                    #         items.append({
                    #             "s_warehouse": s_warehouse,
                    #             "t_warehouse": "Work In Progress - TKFOC",
                    #             "item_code": jc.production_item,
                    #             "qty": min(flt(batch_qty), remaining),
                    #             "uom": bom_doc.items[0].uom,
                    #             "stock_uom": bom_doc.items[0].stock_uom,
                    #             "batch_no": b,
                    #             "job_card": jc.name
                    #         })
                    #         remaining -= min(flt(batch_qty), remaining)
                if remaining <= 0:
                    break

    # Add remaining BOM items from JS-provided item_details
    for j in item_details:
        if j["item_code"] == first_item.item_code:
            continue
        items.append({
            "s_warehouse": "Stores - TKFOC",
            "t_warehouse": "Work In Progress - TKFOC",
            "item_code": j["item_code"],
            "uom": j.get("uom") or j.get("stock_uom"),
            "stock_uom": j.get("stock_uom"),
            "qty": j["required_qty"]
        })

    return items



@frappe.whitelist()
def create_transfer_stock_entry_ja(bom,item_details, work_order):
    if isinstance(item_details, str):
        item_details = json.loads(item_details)
    bom_doc = frappe.get_doc("BOM", bom)
    first_item = frappe.get_all(
        "BOM Item",
        filters={"parent": bom, "idx": 1},
        fields=["item_code", "qty", "bom_no"],
        limit=1
    )

    if not first_item:
        frappe.throw("No items found in this BOM")

    first_item = first_item[0]
    job_cards = frappe.get_all(
        "Job Card",
        filters={
            "bom_no": first_item.bom_no,
            "docstatus": 1,
            "status": "Completed"
        },
        fields=["name", "for_quantity", "custom_batch_no", "custom_all_batch_nos", "production_item","work_order"]
    )



    items = []

    first_item_required_qty = 0
    for j in item_details:
        if j["item_code"] == first_item.item_code:
            first_item_required_qty = flt(j["required_qty"])
            break
    remaining = first_item_required_qty

    for idx, item in enumerate(bom_doc.items):
        if idx == 0:
            for jc in job_cards:
                if frappe.db.get_value("Work Order",jc.work_order,"production_plan")== frappe.db.get_value("Work Order",work_order,"production_plan"):
                    s_warehouse = frappe.db.get_value("Work Order", jc.work_order, "fg_warehouse") or "Stranding - TKFOC"
                    all_batches = [b.strip() for b in (jc.custom_all_batch_nos or "").split(",") if b.strip()]
                    if not all_batches:
                        all_batches = [jc.custom_batch_no] if jc.custom_batch_no else []
                    for b in all_batches:
                        if remaining <= 0:
                            break
                        batch_qty = frappe.db.get_value("Batch", b, "batch_qty") if frappe.db.exists("Batch", b) else 0
                        if batch_qty > 0:
                            items.append({
                                "s_warehouse": s_warehouse,
                                "t_warehouse": "Work In Progress - TKFOC",
                                "item_code": jc.production_item,
                                "qty": min(flt(batch_qty), remaining),
                                "uom":item.uom,
                                "stock_uom":item.stock_uom,
                                "batch_no": b,
                                "job_card": jc.name
                            })
                            remaining -= min(flt(batch_qty), remaining)
                if remaining <= 0:
                    break
    for j in item_details:
        if j["item_code"] == first_item.item_code:
            continue
        items.append({
            "s_warehouse": "Stores - TKFOC",
            "t_warehouse": "Work In Progress - TKFOC",
            "item_code": j["item_code"],
            "uom": j.get("uom") or j.get("stock_uom"),
            "stock_uom": j.get("stock_uom"),
            "qty": j["required_qty"]
        })

    return items

@frappe.whitelist()
def delete_stock_entry(doc, method):
    frappe.db.sql("""
        UPDATE `tabStock Entry`
        SET job_card = %s
        WHERE work_order = %s and stock_entry_type = "Manufacture"
    """, (doc.custom_job_card, doc.work_order))