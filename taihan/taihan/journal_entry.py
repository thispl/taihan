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

# update employee expense in MIS while submit Journal Entry
@frappe.whitelist()
def update_expenses(doc,method):
    if doc.voucher_type=="Journal Entry":
        if doc.accounts:
            for i in doc.accounts:
                if i.account=="Employee Joining Expense - TKFCCD" and i.party_type=="Employee":
                    emp=frappe.get_doc("Employee",{"name":i.party})
                    emp.append("custom_expense",{
                        "expense":doc.user_remark,
                        "expense_amount":i.debit_in_account_currency,
                        "date":doc.posting_date,
                        "journal_entry":doc.name
                    })
                    emp.save()
    frappe.db.commit()



@frappe.whitelist()
def update_employee(employee):
    return frappe.db.get_value("Employee",{"name":employee},["first_name"])


# update employee expense in MIS while cancel Journal Entry
@frappe.whitelist()
def update_expenses_cancel(doc,method):
    if doc.voucher_type=="Journal Entry":
        if doc.accounts:
            for i in doc.accounts:
                if i.account=="Employee Joining Expense - TKFCCD" and i.party_type=="Employee":
                    emp=frappe.get_doc("Employee",{"name":i.party})
                    emp.custom_expense = [
                            row for row in emp.custom_expense if row.journal_entry != doc.name
                        ]
                    for idx, row in enumerate(emp.custom_expense, start=1):
                        row.idx = idx
                    emp.save()
    frappe.db.commit()