from __future__ import unicode_literals
from functools import total_ordering
from itertools import count
import frappe
from frappe import permissions
from frappe.utils import cstr, cint, getdate, get_last_day, get_first_day, add_days, date_diff
from math import floor
from frappe import msgprint, _
from calendar import month, monthrange
from datetime import date, timedelta, datetime, time

# Correct the duplicate key in status_map
status_map = {
    "Absent": "A",
    "Half Day": "HD",
    "Present": "P",
    "None" : "",
    "Leave Without Pay": "LOP",
    "Casual Leave": "CL",
    "Compensatory Off": "C-OFF",
    "Medical Leave":"ML",
    "Emergency Leave":"EmL",
    "Hajj Leave":"HL",
    "Umrah Leave":"UL",
    "Annual Leave":"AL",
    
}

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    columns = [
        _("Employee ID") + ":Data/:150",
        _("Employee Name") + ':Data:100',
        _("Department") + ":Data/:150",
        _("DOJ") + ":Date/:100",
        _("Status") +":Data/:100"
    ]
    dates = get_dates(filters.from_date, filters.to_date)
    for date in dates:
        date = datetime.strptime(date, '%Y-%m-%d')
        day = date.strftime('%d')
        month = date.strftime('%b')
        columns.append(_(f"{day}/{month}") + ":Data/:70")
    columns.append(_("Payment Days") + ":Data/:100")
    columns.append(_("Present") + ":Data/:100")
    columns.append(_("Half Day") + ":Data/:100")
    columns.append(_('Paid Leave')+ ':Data/:150')
    columns.append(_('Paid Holiday')+ ':Data/:100')
    columns.append(_('Weekoff')+ ':Data/:100')
    # columns.append(_('COFF')+ ':Data/:100')
    columns.append(_("Absent") + ":Data/:100")
    columns.append(_('LOP')+ ':Data/:100')
    return columns

def get_data(filters):
    data = []
    employees = get_employees(filters)
    dates = get_dates(filters.from_date, filters.to_date)
    total_present = 0
    total_half_day = 0
    total_paid_leave = 0
    total_lop = 0
    total_absent = 0
    total_weekoff = 0
    total_holiday = 0
    for emp in employees:
        # Initialize rows for each employee
        row1 = [emp.name, emp.employee_name, emp.department, emp.date_of_joining," "]
        row2 = ["", "", ""," ","In Time"]
        row3 = ["", "", "","","Out Time"]
        row4 = ["", "", "","","Shift"]
        row5 = ["", "", "","","TWH"]
        row6 = ["", "", "", "","OT"]
        row7 = ["", "", "","", "Late"]
        row8 = ["", "", "","", "Early Out"]
        
        # Iterate through each date in the range
        for date in dates:
            att = frappe.db.get_value(
                "Attendance",
                {'attendance_date': date, 'employee': emp.name, 'docstatus': ('!=', '2')},
                ['status', 'in_time', 'out_time', 'shift', 'custom_total_working_hours', 'leave_type', 'employee',
                 'attendance_date', 'name', 'late_entry', "leave_application", 'custom_late_entry_time', 'custom_early_exit_time','custom_ot_hours']
            )

            # Ensure att is not None and has enough data to avoid index errors
            if att:
                status = status_map.get(att[0], "")
                # Append data to rows if attendance record exists and has enough elements
                row2.append(att[1] if att[1] else "-")
                row3.append(att[2] if att[2] else "-")
                row4.append(att[3] if att[3] else "-")
                row5.append(att[4] if att[4] else "-")
                row6.append(att[13] if att[6] else "-")
                row7.append(att[11] if att[9] else "-")
                row8.append(att[12] if att[10] else "-")
                if att[0] == "Present":
                    total_present +=1
                    row1.append("P")
                elif att[0] == "Half Day":
                    hh = check_holiday(date,emp.name)
                    if hh:
                        if hh == 'WW':
                            
                            row1.append(hh)
                            total_weekoff += 1
                        elif hh == 'HH':
                            row1.append(hh)
                            total_holiday += 1
                    elif[5]:
                        leave_applications = frappe.db.sql("""
                            SELECT leave_type 
                            FROM `tabLeave Application` 
                            WHERE from_date=%s AND employee=%s AND status='Approved'
                        """, (date, emp.name), as_dict=True)

                        if len(leave_applications) > 1:
                            leave_types = []
                            leave_type_map = {
                                
                                "Compensatory Off": "COFF",
                                "Casual Leave": "CL",
                                
                                "Leave Without Pay": "LOP"
                            }
                            
                            for leave in leave_applications:
                                leave_type_code = leave_type_map.get(leave['leave_type'], leave['leave_type'])
                                leave_types.append(leave_type_code)
                                if leave['leave_type'] == "Leave Without Pay":
                                    
                                    total_lop += 0.5
                                else:
                                    total_paid_leave += 0.5
                            
                            lstatus = "/".join(leave_types)
                            row1.append(lstatus)

                        elif att[5] and att[1] and att[2]:
                            if att[4] >= timedelta(hours=4):        
                                if att[5] == "Compensatory Off":
                                    row1.append('P/COFF')
                                    total_half_day = total_half_day + 0.5
                                    total_paid_leave = total_paid_leave + 0.5
                                    total_present=total_present+ 0.5		
                                elif att[5] == "Casual Leave":
                                    row1.append('P/CL')
                                    total_half_day = total_half_day + 0.5
                                    total_present=total_present+ 0.5
                                    total_paid_leave = total_paid_leave + 0.5		
                                    
                                elif att[5] == "Leave Without Pay":
                                    row1.append('P/LOP')
                                    total_half_day = total_half_day + 0.5
                                    total_present=total_present+ 0.5
                                    
                                elif att[5] == "Annual Leave":
                                    row1.append('P/AL')
                                    total_half_day = total_half_day + 0.5
                                    total_present=total_present+ 0.5
                                elif att[5] == "Medical Leave":
                                    row1.append('P/ML')
                                    total_half_day = total_half_day + 0.5
                                    total_present=total_present+ 0.5
                                    
                                elif att[5] == "Hajj Leave":
                                    row1.append('P/HL')
                                    total_half_day = total_half_day + 0.5
                                    total_present=total_present+ 0.5
                                    
                                elif att[5] == "Umrah Leave":
                                    row1.append('P/UL')
                                    total_half_day = total_half_day + 0.5
                                    total_present=total_present+ 0.5
                                    
                                elif att[5] == "Emergency Leave":
                                    row1.append('P/EmL')
                                    total_half_day = total_half_day + 0.5
                                    total_present=total_present+ 0.5
                                    
                                else:
                                    row1.append('P/L')
                                    total_half_day = total_half_day + 0.5
                                    total_present=total_present+ 0.5
                                    total_lop += 0.5
                            elif att[4] <=4:    
                                if att[5] == "Compensatory Off":
                                    row1.append('A/COFF')
                                    total_half_day = total_half_day + 0.5
                                    total_present=total_present+ 0.5
                                    total_paid_leave = total_paid_leave + 0.5	
                                elif att[5] == "Casual Leave":
                                    row1.append('A/CL')
                                    total_half_day = total_half_day + 0.5
                                    total_present=total_present+ 0.5
                                    total_paid_leave = total_paid_leave + 0.5	
                            
                                elif att[5] == "Leave Without Pay":
                                    row1.append('A/LOP')
                                    total_half_day = total_half_day + 0.5
                                    total_present=total_present+ 0.5
                                    total_lop += 0.5
                                elif att[5] == "Annual Leave":
                                    row1.append('A/AL')
                                    total_half_day = total_half_day + 0.5
                                    total_present=total_present+ 0.5
                                elif att[5] == "Medical Leave":
                                    row1.append('A/ML')
                                    total_half_day = total_half_day + 0.5
                                    total_present=total_present+ 0.5
                                elif att[5] == "Hajj Leave":
                                    row1.append('A/HL')
                                    total_half_day = total_half_day + 0.5
                                    total_present=total_present+ 0.5
                                elif att[5] == "Umrah Leave":
                                    row1.append('A/UL')
                                    total_half_day = total_half_day + 0.5
                                    total_present=total_present+ 0.5
                                elif att[5] == "Emergency Leave":
                                    row1.append('A/EmL')
                                    total_half_day = total_half_day + 0.5
                                    total_present=total_present+ 0.5
                                else:
                                    row1.append('A/P')
                                    total_half_day = total_half_day + 0.5
                                    total_present=total_present+ 0.5
                                    total_lop += 0.5 
                            else:
                                if att[5]:
                                    
                                    if att[5] == "Compensatory Off":
                                        row1.append('P/COFF')
                                        total_paid_leave = total_paid_leave + 0.5
                                        total_present=total_present+ 0.5	
                                    elif att[5] == "Casual Leave":
                                        row1.append('P/CL')
                                        total_paid_leave = total_paid_leave + 0.5
                                        total_present=total_present+ 0.5	
                                    
                                    elif att[5] == "Leave Without Pay":
                                        row1.append('P/LOP')
                                        total_present=total_present+ 0.5
                                        total_lop += 0.5
                                    elif att[5] == "Annual Leave":
                                        row1.append('P/AL')
                                        total_half_day = total_half_day + 0.5
                                        total_present=total_present+ 0.5
                                        
                                    elif att[5] == "Medical Leave":
                                        row1.append('P/ML')
                                        total_half_day = total_half_day + 0.5
                                        total_present=total_present+ 0.5
                                        
                                    elif att[5] == "Hajj Leave":
                                        row1.append('P/HL')
                                        total_half_day = total_half_day + 0.5
                                        total_present=total_present+ 0.5
                                        
                                    elif att[5] == "Umrah Leave":
                                        row1.append('P/UL')
                                        total_half_day = total_half_day + 0.5
                                        total_present=total_present+ 0.5
                                        
                                    elif att[5] == "Emergency Leave":
                                        row1.append('P/EmL')
                                        total_half_day = total_half_day + 0.5
                                        total_present=total_present+ 0.5
                                        
                                    else:
                                        row1.append('A/L')
                                        total_present=total_present+ 0.5
                                        total_lop += 0.5
                                else:
                                    
                                    if att[5] == "Compensatory Off":
                                        row1.append('A/COFF')
                                        total_paid_leave = total_paid_leave + 0.5
                                        total_absent=total_absent+ 0.5	
                                    elif att[5] == "Casual Leave":
                                        row1.append('A/CL')
                                        total_paid_leave = total_paid_leave + 0.5
                                        total_absent=total_absent+ 0.5	
                                        
                                    elif att[5] == "Leave Without Pay":
                                        row1.append('A/LOP')
                                        total_absent=total_absent+ 0.5
                                        total_lop += 0.5
                                    elif att[5] == "Annual Leave":
                                        row1.append('A/AL')
                                        total_half_day = total_half_day + 0.5
                                        total_present=total_present+ 0.5
                                        
                                    elif att[5] == "Medical Leave":
                                        row1.append('A/ML')
                                        total_half_day = total_half_day + 0.5
                                        total_present=total_present+ 0.5
                                        
                                    elif att[5] == "Hajj Leave":
                                        row1.append('A/HL')
                                        total_half_day = total_half_day + 0.5
                                        total_present=total_present+ 0.5
                                        
                                    elif att[5] == "Umrah Leave":
                                        row1.append('A/UL')
                                        total_half_day = total_half_day + 0.5
                                        total_present=total_present+ 0.5
                                        
                                    elif att[5] == "Emergency Leave":
                                        row1.append('A/EmL')
                                        total_half_day = total_half_day + 0.5
                                        total_present=total_present+ 0.5
                                        
                                    else:
                                        row1.append('A/L')
                                        total_absent=total_absent+ 0.5
                                        total_lop += 0.5
                               
                        elif att[5] and not att[2] or not att[1]:
                            
                            if att[5] == "Compensatory Off":
                                row1.append('A/COFF')
                                total_paid_leave = total_paid_leave + 0.5
                                total_absent=total_absent+ 0.5	
                            elif att[5] == "Casual Leave":
                                row1.append('A/CL')
                                total_paid_leave = total_paid_leave + 0.5
                                total_absent=total_absent+ 0.5	
                        
                            elif att[5] == "Leave Without Pay":
                                row1.append('A/LOP')
                                total_lop = total_lop + 0.5
                                total_absent=total_absent+ 0.5
                            elif att[5] == "Annual Leave":
                                row1.append('A/AL')
                                total_half_day = total_half_day + 0.5
                                total_present=total_present+ 0.5
                                
                            elif att[5] == "Medical Leave":
                                row1.append('A/ML')
                                total_half_day = total_half_day + 0.5
                                total_present=total_present+ 0.5
                                
                            elif att[5] == "Hajj Leave":
                                row1.append('A/HL')
                                total_half_day = total_half_day + 0.5
                                total_present=total_present+ 0.5
                                
                            elif att[5] == "Umrah Leave":
                                row1.append('A/UL')
                                total_half_day = total_half_day + 0.5
                                total_present=total_present+ 0.5
                                
                            elif att[5] == "Emergency Leave":
                                row1.append('A/EmL')
                                total_half_day = total_half_day + 0.5
                                total_present=total_present+ 0.5
                                
                            else:
                                row1.append('A/L')
                                total_lop = total_lop + 0.5
                                total_absent=total_absent+ 0.5
                        
                        

                        else:
                            row1.append('P/A')
                            total_half_day = total_half_day + 0.5
                            total_absent=total_absent+ 0.5
                            total_present = total_present + 0.5
                            
                    else:
                       total_present = total_present + 0.5
                       total_absent=total_absent+ 0.5
                
                elif att[0] == 'Absent':
                    hh = check_holiday(date,emp.name)
                    
                    if hh:
                        # pay +=1
                        if hh == 'WW':
                            
                            row1.append(hh)
                            total_weekoff += 1
                        elif hh == 'HH':
                            row1.append(hh)
                            total_holiday += 1
                        # row1.append(hh)                   
                    else:    
                        row1.append(status)
                        total_absent = total_absent + 1

                elif att[0] == "On Leave":
                        
                    if att[5] == "Compensatory Off":
                        row1.append('COFF')
                        total_paid_leave = total_paid_leave + 1	
                    elif att[5] == "Casual Leave":
                        row1.append('CL')
                        total_paid_leave = total_paid_leave + 1	
                    elif att[5] == "Leave Without Pay":
                        row1.append('LOP')
                        total_lop +=1
                    elif att[5] == "Annual Leave":
                        row1.append('AL')
                        total_paid_leave = total_paid_leave + 1	
                        
                    elif att[5] == "Medical Leave":
                        row1.append('ML')
                        total_paid_leave = total_paid_leave + 1	
                        
                    elif att[5] == "Hajj Leave":
                        row1.append('HL')
                        total_paid_leave = total_paid_leave + 1	
                        
                    elif att[5] == "Umrah Leave":
                        row1.append('UL')
                        total_paid_leave = total_paid_leave + 1	
                        
                    elif att[5] == "Emergency Leave":
                        row1.append('EmL')
                        total_paid_leave = total_paid_leave + 1	
                    else:
                        row1.append('-')
                elif att[5]:
                    hh = check_holiday(date,emp.name)
                    if hh:
                        # pay+=1
                        if hh == 'WW':
                            
                            total_weekoff += 1
                            if att[0] == "Present":
                                weekoff -=1
                            elif att[0] == "Half Day":
                                weekoff -=0.5
                        elif hh == 'HH':
                            total_holiday += 1
                            if att[0] == "Present":
                                weekoff -=1
                            elif att[0] == "Half Day":
                                weekoff -=0.5
                        row1.append(hh)
                    else:    
                        status = status_map.get(att[4], "")
                        total_lop += 1
                        row1.append(status)
                else:
                    row1.append('-')
                
            else:
                # If attendance data is missing or incomplete, append "-" for each column
                row1.append("-")
                row2.append("-")
                row3.append("-")
                row4.append("-")
                row5.append("-")
                row6.append("-")
                row7.append("-")
                row8.append("-")

        row1.extend([total_present+total_weekoff+total_holiday+total_paid_leave,total_present,total_half_day,total_paid_leave,total_holiday,total_weekoff,total_absent,total_lop])
        row2.extend(['-','-','-','-','-','-','-','-'])
        row3.extend(['-','-','-','-','-','-','-','-'])
        row4.extend(['-','-','-','-','-','-','-','-'])
        row5.extend(['-','-','-','-','-','-','-','-'])
        row6.extend(['-','-','-','-','-','-','-','-'])
        row7.extend(['-','-','-','-','-','-','-','-'])
        row8.extend(['-','-','-','-','-','-','-','-'])

        data.append(row1)
        data.append(row2)
        data.append(row3)
        data.append(row4)
        data.append(row5)
        data.append(row6)
        data.append(row7)
        data.append(row8)

    return data

def get_dates(from_date, to_date):
    # Safely calculate date range, include 'from_date' and 'to_date'
    no_of_days = date_diff(add_days(to_date, 1), from_date)
    dates = [add_days(from_date, i) for i in range(no_of_days)]
    return dates

def get_employees(filters):
    conditions = ''
    if filters.employee:
        conditions += f"and employee = '{filters.employee}' "
    
    # Fetching Active and Left employees based on the 'from_date'
    employees = frappe.db.sql(f"""
        SELECT name, employee_name, department, employment_type, date_of_joining 
        FROM `tabEmployee` 
        WHERE status = 'Active' {conditions}
    """, as_dict=True)

    # Employees who have left but are still within the relevant date range
    left_employees = frappe.db.sql(f"""
        SELECT name, employee_name, department, employment_type, date_of_joining 
        FROM `tabEmployee` 
        WHERE status = 'Left' AND relieving_date >= '{filters.from_date}' {conditions}
    """, as_dict=True)

    employees.extend(left_employees)
    return employees


def check_holiday(date,emp):
    holiday_list = frappe.db.get_value('Company','Taihan Kuwait Fiber Optic Cable Company','default_holiday_list')
    holiday = frappe.db.sql("""select `tabHoliday`.holiday_date,`tabHoliday`.weekly_off from `tabHoliday List` 
    left join `tabHoliday` on `tabHoliday`.parent = `tabHoliday List`.name where `tabHoliday List`.name = '%s' and holiday_date = '%s' """%(holiday_list,date),as_dict=True)
    doj= frappe.db.get_value("Employee",{'name':emp},"date_of_joining")
    last= frappe.db.get_value("Employee",{'name':emp},"relieving_date")
    if holiday:
        if last:
            if doj < holiday[0].holiday_date < last:
                if holiday[0].weekly_off == 1:
                    return "WW"
                else:
                    return "HH"
        else:
            if doj < holiday[0].holiday_date:
                if holiday[0].weekly_off == 1:
                    return "WW"
                else:
                    return "HH"