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

#Employee should apply for leave before 30 days when leave type is not leave without pay(not for HR User, HR Manger and HOD) and it will allow when is leave without pay is checked in leave type
@frappe.whitelist()
def validate_leave_application(doc, method):
    today = frappe.utils.today()
    leave_start_date = doc.from_date

    lwp_leave_types = frappe.db.get_all("Leave Type", filters={"is_lwp": 0})
    user_roles = frappe.get_roles(frappe.session.user)

    roles = ["HR User", "HR Manager", "HOD"]

    if not any(role in user_roles for role in roles):
        days_diff = frappe.utils.date_diff(leave_start_date, today)

        for l in lwp_leave_types:
            if l["name"] == doc.leave_type:
                if days_diff < 30:
                    frappe.throw("Employees should apply for leave at least 30 days in advance.")



# Not allow to save if the employee already apply for hajj leave in leave application
@frappe.whitelist()
def validate_hajj_leave(doc,method):
    leave=doc.leave_type
    if leave=="Hajj Leave":
        if frappe.db.exists("Leave Application",{"employee":doc.employee,"leave_type":"Hajj Leave","docstatus":1}):
            frappe.throw("Hajj leave already taken")



# Not allow to save if the employee already apply for Umrah leave for the current year in leave application
@frappe.whitelist()
def validate_umrah_leave_la(doc,method):
    current_year = datetime.now().year
    if doc.leave_type=="Umrah Leave":
        if frappe.db.exists(
            "Leave Application",
            {
                "employee": doc.employee,
                "leave_type": "Umrah Leave",
                "docstatus": 1,
                "from_date": ["between", [f"{current_year}-01-01", f"{current_year}-12-31"]],
            },
        ):
            frappe.throw(_("Employee has already taken Umrah Leave for this year."))