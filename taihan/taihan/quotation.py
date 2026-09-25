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




@frappe.whitelist()
def getstock_detail_warehouse_wise(item_details, company):
    import json
    item_details = json.loads(item_details)
    data = ''
    data += '<h4><center><b>STOCK DETAILS</b></center></h4>'
    data += '<table class="table table-bordered">'

    # First collect all warehouse columns across all items
    all_warehouses = frappe.get_all("Warehouse", filters={"company": company}, fields=["name"])
    all_warehouse_columns = set()

    # Map of item_code -> warehouse -> qty
    item_warehouse_qty = {}

    for j in item_details:
        warehouse_stock_map = {}
        for wh in all_warehouses:
            qty = frappe.db.get_value("Bin", {"item_code": j["item_code"], "warehouse": wh.name}, "actual_qty") or 0
            if qty > 0:
                warehouse_stock_map[wh.name] = qty
                all_warehouse_columns.add(wh.name)
        item_warehouse_qty[j["item_code"]] = {
            "item_name": j["item_name"],
            "warehouse_map": warehouse_stock_map
        }

    # Now write headers
    data += '<tr>'
    data += '<td style="width:13%;border:1px solid black;font-size:12px;background-color:#287887;color:white;"><center><b>ITEM CODE</b></center></td>'
    data += '<td style="width:33%;border:1px solid black;font-size:12px;background-color:#287887;color:white;"><center><b>ITEM NAME</b></center></td>'
    data += '<td style="width:70px;border:1px solid black;font-size:12px;background-color:#287887;color:white;"><center><b>STOCK</b></center></td>'
    for wh in sorted(all_warehouse_columns):
        data += f'<td style="background-color:#287887;color:white;border:1px solid black;"><b>{wh}</b></td>'
    data += '</tr>'

    # Add data rows
    for j in item_details:
        item_code = j["item_code"]
        warehouse_stock = frappe.db.sql("""
            SELECT SUM(b.actual_qty - b.reserved_stock) AS qty
            FROM `tabBin` AS b
            JOIN `tabWarehouse` AS wh ON wh.name = b.warehouse
            JOIN `tabCompany` AS c ON c.name = wh.company
            WHERE b.item_code = %s AND wh.company=%s
        """, (item_code,company), as_dict=True)[0] or {"qty": 0}

        purchase_order = frappe.db.sql("""
            SELECT SUM(poi.qty) as qty
            FROM `tabPurchase Order` po
            JOIN `tabPurchase Order Item` poi ON po.name = poi.parent
            WHERE poi.item_code = %s AND po.docstatus != 2
        """, (item_code,), as_dict=True)[0] or {"qty": 0}

        purchase_receipt = frappe.db.sql("""
            SELECT SUM(pri.qty) as qty
            FROM `tabPurchase Receipt` pr
            JOIN `tabPurchase Receipt Item` pri ON pr.name = pri.parent
            WHERE pri.item_code = %s AND pr.docstatus = 1
        """, (item_code,), as_dict=True)[0] or {"qty": 0}

        in_transit = (purchase_order["qty"] or 0) - (purchase_receipt["qty"] or 0)
        total = (warehouse_stock["qty"] or 0) + in_transit

        data += '<tr>'
        data += f'<td style="text-align:center;border: 1px solid black">{item_code}</td>'
        data += f'<td style="text-align:center;border: 1px solid black">{j["item_name"]}</td>'
        data += f'<td style="text-align:center;border: 1px solid black">{warehouse_stock["qty"] or 0}</td>'
        for wh in sorted(all_warehouse_columns):
            qty = item_warehouse_qty[item_code]["warehouse_map"].get(wh, 0)
            data += f'<td style="text-align:center;border: 1px solid black">{qty}</td>'
        data += '</tr>'

    data += '</table>'
    return data


# send mail for approve the discount percentage while click the request for approval
@frappe.whitelist()
def send_discount_approval(quotation):
    quotation_doc = frappe.get_doc("Quotation", quotation)
    user_roles = frappe.get_roles(frappe.session.user)
    role_hierarchy = {
        "Sales User": "Sales Manager",
        "Sales Manager": "Sales Master Manager",
        "Sales Master Manager": None  # No approval needed
    }
    approver_role = None
    for role in role_hierarchy:
        if role in user_roles:
            approver_role = role_hierarchy[role]
            break  # Stop at the highest matching role
    if not approver_role:
        frappe.msgprint("No approver required for your role.")
        return
    approvers = frappe.get_all("User", filters={"role": approver_role}, fields=["email", "name"])
    for approver in approvers:
        if approver.email:
            frappe.sendmail(
                recipients=approver.email,
                subject=f"Approval Needed: Discount in Quotation {quotation}",
                message=f"A discount of {quotation_doc.additional_discount_percentage}% needs your approval in Quotation {quotation}. Please review."
            )

    frappe.msgprint(f"Approval request sent to {approver_role}(s).")



@frappe.whitelist()
def get_series_with_tax(date,company,doctype):
    company_series = frappe.db.get_value("Company Series",{'company':company,'document_type':doctype,'with_tax':1},'series')
    return company_series


#General Settings Code 
@frappe.whitelist()
def get_series(date,company,doctype):
    company_series = frappe.db.get_value("Company Series",{'company':company,'document_type':doctype,'with_tax':0},'series')
    return company_series


@frappe.whitelist()
def check_discount_percent(discount):
    user_roles = frappe.get_roles(frappe.session.user)
    max_discount = 0
    for role in user_roles:
        d = frappe.db.get_value("Quotation Discount", {'role':role, 'parent': 'Sales Settings'}, ['role', 'max_dis'])
        if d:
            if max_discount < d[1]:
                max_discount = d[1]
    
    if max_discount == 0:
        return 'invalid'
    if float(discount) > max_discount:
        frappe.throw("Maximum discount percentage allowed for you is %s%% "%(int(max_discount)))



# update role based notification for quotation discount %
@frappe.whitelist()
def quotation_notification(doc,method):
    user_roles = frappe.get_roles(frappe.session.user)
    max_discount = 0
    approver_role = None

    # Define role hierarchy
    role_hierarchy = {
        "Sales User": "Sales Manager",
        "Sales Manager": "Sales Master Manager",
        "Sales Master Manager": None  # No approval needed
    }

    for role in user_roles:
        d = frappe.db.get_value("Quotation Discount", {'role': role, 'parent': 'Sales Settings'}, ['role', 'max_dis'])
        if d:
            if max_discount < d[1]:  # Take the max allowed discount among roles
                max_discount = d[1]
                approver_role = role_hierarchy.get(role)

    if max_discount == 0:
        return 'invalid'
    if doc.additional_discount_percentage:
        if float(doc.additional_discount_percentage) > max_discount:
            doc.custom_role = 1  # Set custom_role before throwing an exception
            frappe.msgprint(f"Discount exceeds allowed limit. Approval required from {approver_role}.")
        else:
            doc.custom_role=0
    else:
        doc.custom_role=0



# validate the quotation while submit the quotation
@frappe.whitelist()
def quotation_notification_before_submit(doc,method):
    user_roles = frappe.get_roles(frappe.session.user)
    max_discount = 0
    approver_role = None

    # Define role hierarchy
    role_hierarchy = {
        "Sales User": "Sales Manager",
        "Sales Manager": "Sales Master Manager",
        "Sales Master Manager": None  # No approval needed
    }

    for role in user_roles:
        d = frappe.db.get_value("Quotation Discount", {'role': role, 'parent': 'Sales Settings'}, ['role', 'max_dis'])
        if d:
            if max_discount < d[1]: 
                max_discount = d[1]
                approver_role = role_hierarchy.get(role)

    if max_discount == 0:
        return 'invalid'

    if doc.custom_role==1:
        frappe.throw(f"Maximum discount percentage allowed for you is {int(max_discount)}%.Discount exceeds allowed limit. Approval required from {approver_role}.")