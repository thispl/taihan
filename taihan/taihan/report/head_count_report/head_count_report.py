# Copyright (c) 2025, Teampro and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt
import erpnext


def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
    shift_types = frappe.get_all("Shift Type", pluck="name")
    columns = [
        _("Department") + ":Link/Department:110",
    ]
    for shift in shift_types:
        columns.append(_(f"{shift} Count") + ":Data/:150")
    columns.append(_("Total") + ":Data/:150")
    for shift in shift_types:
        columns.append(_(f"{shift} Overtime Hrs") + ":Data/:150")

    columns.append(_("Total Overtime") + ":Data/:150")

    return columns


def get_data(filters):
    data = []
    
    # Fetch all distinct departments from attendance records
    departments = frappe.db.sql("""
        SELECT DISTINCT department
        FROM `tabAttendance`
        WHERE attendance_date BETWEEN %s AND %s
        AND docstatus != 2
    """, (filters.from_date, filters.to_date), as_dict=True)
    
    # Fetch all shift types
    shifts = frappe.get_all("Shift Type", pluck="name")

    for dept in departments:
        department = dept.department
        shift_counts = {shift: {"count": 0, "overtime": 0} for shift in shifts}
        total_count = 0
        total_overtime = 0
        
        # Fetch attendance counts and overtime per shift
        attendance_data = frappe.db.sql("""
            SELECT shift, COUNT(status) AS shift_count, 
                   SUM(custom_ot_hours) AS shift_overtime
            FROM `tabAttendance`
            WHERE attendance_date BETWEEN %s AND %s
            AND docstatus != 2
            AND in_time IS NOT NULL
            AND department = %s
            GROUP BY shift
        """, (filters.from_date, filters.to_date, department), as_dict=True)

        # Update shift_counts dictionary
        for record in attendance_data:
            shift_name = record.shift
            if shift_name in shift_counts:
                shift_counts[shift_name]["count"] = record.shift_count or 0
                shift_counts[shift_name]["overtime"] = round(flt(record.shift_overtime or 0) / 10000, 2)

                total_count += shift_counts[shift_name]["count"]
                total_overtime += shift_counts[shift_name]["overtime"]

        # Construct row with correct column order
        row = [department]
        for shift in shifts:
            row.append(shift_counts[shift]["count"])
        row.append(total_count)
        for shift in shifts:
            row.append(shift_counts[shift]["overtime"])
        row.append(round(total_overtime, 2))
        data.append(row)

    return data
