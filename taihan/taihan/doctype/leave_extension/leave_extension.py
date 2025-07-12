# Copyright (c) 2025, Teampro and contributors
# For license information, please see license.txt

# import frappefrom frappe.model.document import Document

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
from dateutil.relativedelta import relativedelta
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
from frappe.model.document import Document
from frappe.utils import getdate


class LeaveExtension(Document):
    #While submit this document , create the leave Application for extension dates
    def on_submit(self):
    #     # Create a new Leave Application
    #     leave = frappe.new_doc("Leave Application")
    #     leave.employee = self.employee
    #     leave.employee_name = self.employee_name
    #     leave.leave_type = self.leave_type
    #     leave.company = self.company
    #     leave.from_date = self.extension_from_date
    #     leave.to_date = self.extension_to_date
    #     leave.description = "Late Rejoin"
    #     leave.status = "Approved"
    #     leave.ticket_required = "Not Required"
        
    #     leave.save(ignore_permissions=True)
    #     leave.submit()

    #     frappe.db.commit()
        leave_type_allocation = frappe.db.get_value("Leave Type", self.leave_type, "max_leaves_allowed")
        total_leave_taken = frappe.db.sql("""
            SELECT SUM(total_leave_days) FROM `tabLeave Application`
            WHERE employee = %s
            AND leave_type = %s
            AND status = 'Approved'
        """, (self.employee, self.leave_type))

        total_leave_taken = total_leave_taken[0][0] if total_leave_taken and total_leave_taken[0][0] else 0
        available_leave_balance = leave_type_allocation - total_leave_taken if leave_type_allocation else 0
        total_days_requested = (getdate(self.extension_to_date) - getdate(self.extension_from_date)).days + 1
        days_under_balance = min(total_days_requested, max(available_leave_balance, 0))  # Ensure non-negative
        remaining_days = total_days_requested - days_under_balance
        if days_under_balance > 0:
            leave = frappe.new_doc("Leave Application")
            leave.employee = self.employee
            leave.employee_name = self.employee_name
            leave.leave_type = self.leave_type
            leave.company = self.company
            leave.from_date = self.extension_from_date
            leave.to_date = add_days(self.extension_from_date, days_under_balance - 1)
            leave.description = "Extension Leave - Covered by balance"
            leave.status = "Approved"
            leave.ticket_required = "Not Required"

            leave.save(ignore_permissions=True)
            leave.submit()
        if remaining_days > 0:
            leave = frappe.new_doc("Leave Application")
            leave.employee = self.employee
            leave.employee_name = self.employee_name
            leave.leave_type = "Leave Without Pay"
            leave.company = self.company
            leave.from_date = add_days(self.extension_from_date, days_under_balance)
            leave.to_date = self.extension_to_date
            leave.description = "Extension Leave - Leave Without Pay"
            leave.status = "Approved"
            leave.ticket_required = "Not Required"

            leave.save(ignore_permissions=True)
            leave.submit()
        frappe.db.commit()



       
    #While cancel this document , the extension dates attendance will be cancel
    def on_cancel(self):
        attendance_list = frappe.get_all(
            "Attendance",
            filters={
                "employee": self.employee,
                "attendance_date": ["between", [self.extension_from_date, self.extension_to_date]],
                "docstatus": ["!=", 2] 
            },
            fields=["name", "docstatus"]
        )

        for attendance in attendance_list:
            attendance_doc = frappe.get_doc("Attendance", attendance.name)
            if attendance_doc.docstatus == 1:
                attendance_doc.cancel()
        frappe.db.commit()


#While enter the employee in leave extension get the values (Name , from date and to date) from Leave Application and set it
@frappe.whitelist()
def get_leave_details_le(employee):
    leave_application = frappe.get_list(
        "Leave Application",
        filters={
            "employee": employee,
            "status": "Approved",
            "leave_type":("In",("Annual Leave","Leave Without Pay"))
        },
        fields=["name", "from_date", "to_date"],
        order_by="creation desc",
        limit=1
    )
    if leave_application:
        leave_details = leave_application[0]
        return {
            "leave_application": leave_details.name,
            "from_date": leave_details.from_date,
            "to_date": leave_details.to_date
        }

    else:
        frappe.throw(_("No approved annual leave application found for the employee."))