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

# validate Hajj leave allocation 
@frappe.whitelist()
def validate_hajj_allocation(employee,leave_type,name):
    frappe.errprint("Hello")
    if frappe.db.exists("Leave Allocation",{"employee":employee,"leave_type":leave_type,"docstatus":("!=",2),"name":("!=",name)}):
        return True
    return False



@frappe.whitelist()
def validate_umrah_leave(from_date,to_date):
    current_year = datetime.now().year
    current_from_date = f"{current_year}-01-01"
    current_to_date=f"{current_year}-12-31"
    if from_date!=current_from_date and to_date!=current_to_date:
        return "True"
    return "False"


# validate Umrah leave allocation 
@frappe.whitelist()
def validate_umrah_allocation(employee,leave_type,name,from_date,to_date):
    exists = frappe.db.exists(
        "Leave Allocation",
        {
            "employee": employee,
            "leave_type": leave_type,
            "from_date": from_date,
            "to_date": to_date,
            "docstatus": ("!=", 2),
            "name":("!=",name)
        },
    )
    return bool(exists) 
    # if frappe.db.exists("Leave Allocation",{"employee":employee,"leave_type":leave_type,"from_date":from_date,"to_date":to_date,"docstatus":("!=",2),"name":("!=",name)}):
    #     return bool(exists)
