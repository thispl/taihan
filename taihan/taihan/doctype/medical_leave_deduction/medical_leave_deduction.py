# Copyright (c) 2025, Teampro and contributors
# For license information, please see license.txt

# import frappe
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
import frappe,erpnext

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


class MedicalLeaveDeduction(Document):
    pass


@frappe.whitelist()
def leave_deduction(from_date, to_date):
    from datetime import datetime

    if isinstance(from_date, str):
        from_date = datetime.strptime(from_date, "%Y-%m-%d")
    if isinstance(to_date, str):
        to_date = datetime.strptime(to_date, "%Y-%m-%d")

    year_start_date = from_date.replace(month=1, day=1)

    # Fetch all relevant attendance records
    attendance_records = frappe.get_all(
        "Attendance",
        filters={
            "docstatus": ("!=", 2),
            "leave_type": "Medical Leave",
            "attendance_date": ("between", (year_start_date, to_date)),
        },
        fields=["employee", "status"]
    )

    # Initialize a dictionary to hold counts per employee
    employee_leave_count = {}

    # Calculate leave count per employee
    for att in attendance_records:
        employee = att["employee"]
        if employee not in employee_leave_count:
            employee_leave_count[employee] = 0

        if att["status"] == "On Leave":
            employee_leave_count[employee] += 1
        elif att["status"] == "Half Day":
            employee_leave_count[employee] += 0.5

    # Iterate through employees to calculate deductions
    for employee, count in employee_leave_count.items():

        # Fetch salary and company details for the employee
        salary, company = frappe.db.get_value(
            "Employee", {"name": employee}, ["ctc", "company"]
        )

        # Ensure salary is fetched and calculate deductions
        if not salary:
            frappe.throw(f"Salary information is missing for Employee: {employee}")

        deduction = 0
        if 15 < count <= 25:
            deduction = (3 / 4) * (salary / 26)
        elif 25 < count <= 35:
            deduction = (1 / 2) * (salary / 26)
        elif 35 < count <= 45:
            deduction = (1 / 4) * (salary / 26)
        elif count >45:
            deduction = salary

        if deduction > 0:
            # Create Additional Salary record
            add = frappe.new_doc("Additional Salary")
            add.company = company
            add.employee = employee
            add.salary_component = "Medical Leave Deduction"
            add.amount = deduction
            add.payroll_date = from_date
            add.save(ignore_permissions=True)
            add.submit()
            frappe.msgprint(f"Additional Salary has been created for Employee: {employee}")

    frappe.msgprint("All deductions have been processed.")

        

    