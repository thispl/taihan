# Taihan Current mark_attendance.py

from __future__ import print_function
from pickle import TRUE
from time import strptime
from traceback import print_tb
import frappe
from frappe.utils.data import ceil, get_time, get_year_start
# import pandas as pd
import json
import datetime
from frappe.utils import (getdate, cint, add_months, date_diff, add_days,
    nowdate, get_datetime_str, cstr, get_datetime, now_datetime, format_datetime)
from datetime import datetime
from calendar import monthrange
from frappe import _, msgprint
from frappe.utils import flt
from frappe.utils import cstr, cint, getdate,get_first_day, get_last_day, today, time_diff_in_hours
import requests
from datetime import date, timedelta,time
from datetime import datetime, timedelta
from frappe.utils import get_url_to_form
import math
import dateutil.relativedelta
import datetime as dt
from datetime import datetime, timedelta

status_map = {
    "Present": "P",
    "Absent": "A",
    "Half Day": "HD",
    "On Leave":"On Leave",
    "Work From Home": "WFH",
    "Holiday": "HH",
    "Weekly Off": "WW",
    "Leave Without Pay": "LOP",
    "Casual Leave": "CL",
    "Earned Leave": "EL",
    "ESI Leave": "ESI",
    "Compensatory Off": "C-OFF",
}

def get_dates(from_date,to_date):
    no_of_days = date_diff(add_days(to_date, 1), from_date)
    dates = [add_days(from_date, i) for i in range(0, no_of_days)]
    return dates

@frappe.whitelist()
def mark_att_process():
    # from_date = add_days(today(),-1)  
    # to_date = today()
    from_date="2025-01-29"
    to_date="2025-01-29"
    dates = get_dates(from_date,to_date)
    mark_att(from_date,to_date)    
    return "ok"

@frappe.whitelist()
def mark_att(from_date,to_date):
    # from_date="2025-01-20"
    # to_date="2025-01-20"
    checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where date(time) between '%s' and '%s' order by time ASC """%(from_date,to_date),as_dict=True)
    for c in checkins:
        employee = frappe.db.exists('Employee',{'status':'Active','date_of_joining':['<=',from_date],'name':c.employee})
        if employee:
            att = mark_attendance_from_checkin(c.employee,c.time,c.log_type)
            if att:
                frappe.db.set_value("Employee Checkin",c.name, "skip_auto_attendance", "1")
    mark_absent(from_date,to_date)
    mark_wh(from_date,to_date)
    mark_late_entry(from_date,to_date)
    mark_early_out(from_date,to_date)
    ot_calculation(from_date,to_date)
    update_ot_request(from_date,to_date)
    
    
# @frappe.whitelist()
# def mark_attendance_from_checkin(employee,time,log_type):
#     att_date = time.date()
#     att_time = time.time()
#     shift = ''
#     if log_type == 'IN' and datetime.strptime('07:30:00', '%H:%M:%S').time() < att_time < datetime.strptime('15:30:00', '%H:%M:%S').time():
#         checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'IN' and date(time) = '%s' and time(time) between "07:30:00" and "15:30:00" order by time ASC"""%(employee,att_date),as_dict=True)
#         shift1 = frappe.db.get_value('Shift Type',{'name':'Morning shift'},['custom_checkin_start_time','custom_checkin_end_time'])
#         shift_assignment = frappe.db.get_value("Shift Assignment",{"employee":employee,"start_date":att_date},["shift_type"])
#         shift_start_time = frappe.db.get_value('Shift Type',{'name':shift_assignment},['start_time'])
#         value = frappe.db.get_value("Special Occasion",{"date":att_date},["shift"])
#         if (datetime.min + shift1[0]).time() < checkins[0].time.time() < (datetime.min + shift1[1]).time():
#             shift ='Morning shift'
#         elif shift_assignment and shift_start_time:
#             shift_start_time = datetime.min + shift_start_time  # Assuming `start_time` is timedelta
#             if shift_start_time.time() < checkins[0].time.time():
#                 shift = shift_assignment
#         elif value:
#             shift = value
#         else:
#             shift = ''
#         att = frappe.db.exists('Attendance',{"employee":employee,'attendance_date':att_date,'docstatus':['!=','2']})   
#         print(shift)
#         checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'IN' and date(time) = '%s' and time(time) between "07:30:00" and "15:30:00" order by time ASC"""%(employee,att_date),as_dict=True)
#         if not att and checkins:
#             shift_assignment = frappe.db.get_value("Shift Assignment",{"employee":employee,"start_date":att_date},["shift_type"])
#             att = frappe.new_doc("Attendance")
#             att.employee = employee
#             att.attendance_date = att_date
#             att.shift = shift
#             att.custom_assigned_shift = shift_assignment
#             att.status = 'Absent'
#             att.in_time = checkins[0].time
#             att.custom_late_entry_time = "00:00:00"
#             att.custom_early_exit_time = "00:00:00"
#             att.custom_total_working_hours="00:00:00"
#             att.custom_ot_hours="00:00:00"
#             att.working_hours = "0.0"
#             att.save(ignore_permissions=True)
#             frappe.db.commit()
#             for c in checkins:
#                 frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
#                 frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
#         else:
#             shift_assignment = frappe.db.get_value("Shift Assignment",{"employee":employee,"start_date":att_date},["shift_type"])
#             att = frappe.get_doc("Attendance",att)
#             print(att.name)
#             if att.docstatus == 0:
#                 att.employee = employee
#                 att.attendance_date = att_date
#                 att.shift = shift
#                 att.custom_assigned_shift = shift_assignment
#                 att.in_time = checkins[0].time
#                 att.working_hours = "0.0"
#                 att.custom_total_working_hours="00:00:00"
#                 att.custom_ot_hours="00:00:00"
#                 att.save(ignore_permissions=True)
#                 frappe.db.commit()
#                 for c in checkins:
#                     print(c.name)
#                     frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
#                     frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
#                 return att 
#     if log_type == 'OUT':
#         max_out = datetime.strptime('10:30','%H:%M').time()
#         in_time = frappe.db.get_value("Attendance",{"employee":employee,"attendance_date":att_date},["in_time"])
#         if att_time < max_out:
#             if in_time and in_time.time() < max_out and att_time > in_time.time():
#                 checkins = frappe.db.sql("select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'OUT' and date(time) = '%s' and time(time)<'%s' order by time ASC "%(employee,att_date,max_out),as_dict=True)
#                 att = frappe.db.exists("Attendance",{'employee':employee,'attendance_date':att_date})
#                 if att:
#                     att = frappe.get_doc("Attendance",att)
#                     if att.docstatus == 0:
#                         if not att.shift:
#                             if len(checkins) > 0:
#                                 att.shift = get_actual_shift(get_time(checkins[-1].time),employee,att_date)
#                                 att.out_time = checkins[-1].time
#                                 for c in checkins:
#                                     frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
#                                     frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
#                             else:
#                                 if not att.shift:
#                                     att.shift = get_actual_shift(get_time(checkins[-1].time),employee,att_date)
#                                     att.out_time = checkins[0].time
#                                 frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
#                                 frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
#                         else:
#                             if len(checkins) > 0:
#                                 att.out_time = checkins[-1].time
#                                 for c in checkins:
#                                     frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
#                                     frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
#                             else:
#                                 att.out_time = checkins[0].time
#                                 frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
#                                 frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
#                         att.save(ignore_permissions=True)
#                         frappe.db.commit()
#                 else:
#                     shift_assignment = frappe.db.get_value("Shift Assignment",{"employee":employee,"start_date":att_date},["shift_type"])
#                     att = frappe.new_doc("Attendance")
#                     att.employee = employee
#                     att.attendance_date = att_date
#                     att.shift = shift
#                     att.custom_assigned_shift = shift_assignment
#                     att.status = 'Absent'
#                     att.custom_ot_hours = "00:00:00"
#                     if len(checkins) > 0:
#                         if not att.shift:
#                             att.shift = get_actual_shift(get_time(checkins[-1].time),employee,att_date)
#                         att.out_time = checkins[-1].time
#                         for c in checkins:
#                             frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
#                             frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
#                     else:
#                         if not att.shift:
#                             att.shift = get_actual_shift(get_time(checkins[-1].time),att_date)
#                         att.out_time = checkins[0].time
#                         frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
#                         frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
#                     att.save(ignore_permissions=True)
#                     frappe.db.commit()
#         else:
#             checkins = frappe.db.sql("select * from `tabEmployee Checkin` where employee ='%s' and log_type = 'OUT' and date(time) = '%s' and time(time)>'%s' order by time ASC"%(employee,att_date,max_out),as_dict=True)
#             att = frappe.db.exists("Attendance",{'employee':employee,'attendance_date':att_date,'docstatus':("!=",2)})
#             if att:
#                 att = frappe.get_doc("Attendance",att)
#                 if att.docstatus == 0:
#                     if not att.shift:
#                         if len(checkins) > 0:
#                             if not att.shift:
#                                 att.shift = get_actual_shift(get_time(checkins[-1].time),employee,att_date)
#                                 att.out_time = checkins[-1].time
#                             for c in checkins:
#                                 frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
#                                 frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
#                         else:
#                             if not att.shift:
#                                 att.shift = get_actual_shift(get_time(checkins[-1].time),employee,att_date)
#                                 att.out_time = checkins[0].time
#                             frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
#                             frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
#                     else:
#                         if len(checkins) > 0:
#                             att.out_time = checkins[-1].time
#                             for c in checkins:
#                                 frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
#                                 frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
#                         else:
#                             att.out_time = checkins[0].time
#                             frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
#                             frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
#                     att.save(ignore_permissions=True)
#                     frappe.db.commit()
#             else:
#                 shift_assignment = frappe.db.get_value("Shift Assignment",{"employee":employee,"start_date":att_date},["shift_type"])
#                 att = frappe.new_doc("Attendance")
#                 att.employee = employee
#                 att.attendance_date = att_date
#                 att.shift = shift
#                 att.custom_assigned_shift = shift_assignment
#                 att.status = 'Absent'
#                 if len(checkins) > 0:
#                     if not att.shift:
#                         att.shift = get_actual_shift(get_time(checkins[-1].time),employee,att_date)
#                     att.out_time = checkins[-1].time
#                     for c in checkins:
#                         frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
#                         frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
#                 else:
#                     if not att.shift:
#                         att.shift = get_actual_shift(get_time(checkins[-1].time),att_date)
#                     att.out_time = checkins[0].time
#                     frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
#                     frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
#                 att.save(ignore_permissions=True)
#                 frappe.db.commit()
                                
def get_actual_shift(get_shift_time,employee,att_date):
    from datetime import datetime
    from datetime import date, timedelta,time
    shift1 = frappe.db.get_value('Shift Type',{'name':'Morning shift'},['start_time','end_time'])
    value = frappe.db.get_value("Special Occasion",{"date":att_date},["shift"])
    if (datetime.min + shift1[0]).time() < get_shift_time < (datetime.min + shift1[0]).time():
        shift = 'Morning shift'
    elif value:
        shift=value
    else:
        shift = ''

    return shift

def mark_absent(from_date,to_date):
    dates = get_dates(from_date,to_date)
    for date in dates:
        employee = frappe.db.get_all('Employee',{'status':'Active','date_of_joining':['<=',from_date]})
        for emp in employee:
            hh = check_holiday(date,emp.name)
            if not hh:
                if not frappe.db.exists('Attendance',{'attendance_date':date,'employee':emp.name,'docstatus':('!=','2')}):
                    att = frappe.new_doc("Attendance")
                    att.employee = emp.name
                    att.status = 'Absent'
                    att.attendance_date = date
                    att.custom_total_working_hours = "00:00:00"
                    att.working_hours = "0.0"
                    att.custom_ot_hours = "00:00:00"
                    att.custom_late_entry_time="00:00:00"
                    att.custom_early_exit_time="00:00:00"
                    att.save(ignore_permissions=True)
                    frappe.db.commit()

def mark_wh(from_date,to_date):
    attendance = frappe.db.get_all('Attendance',{'attendance_date':('between',(from_date,to_date)),'docstatus':('!=','2')},['*'])
    for att in attendance:
        if att.shift and att.in_time and att.out_time :
            if att.in_time and att.out_time:
                in_time = att.in_time
                out_time = att.out_time
            if isinstance(in_time, str):
                in_time = datetime.strptime(in_time, '%Y-%m-%d %H:%M:%S')
            if isinstance(out_time, str):
                out_time = datetime.strptime(out_time, '%Y-%m-%d %H:%M:%S')
            shift_start_time_str = frappe.db.get_value("Shift Type",{"name":att.shift},["start_time"])
            shift_end_time_str = frappe.db.get_value("Shift Type",{"name":att.shift},["end_time"])
            if isinstance(shift_start_time_str, timedelta):
                shift_start_time = (datetime.min + shift_start_time_str).time()
            elif isinstance(shift_start_time_str, str):
                shift_start_time = datetime.strptime(shift_start_time_str, '%H:%M:%S').time()
            else:
                shift_start_time = shift_start_time_str
            if in_time.time() < shift_start_time :
                in_time = datetime.combine(in_time.date(), shift_start_time)
            else:
                in_time = in_time
            shift_end_time_str = frappe.db.get_value("Shift Type", {"name": att.shift}, ["end_time"])
            shift_end_time = (datetime.min + shift_end_time_str).time()
            if att.shift == "Morning shift":
                if out_time.time() > shift_end_time:
                    out_time = datetime.combine(out_time.date(), shift_end_time)
                else:
                    out_time = out_time
            wh = time_diff_in_hours(out_time,in_time)
            if wh:
                wh = round(wh,1)
            default_shift = frappe.db.get_value(
                        "Shift Assignment",
                        {'employee': att.employee, 'start_date': ('<=', att.attendance_date), 'end_date': ('>=', att.attendance_date), "docstatus": 1},
                        ['shift_type']
                    )
            hh = check_holiday(add_days(att.attendance_date,1),att.employee)
            date = check_holiday(att.attendance_date,att.employee)
            if default_shift:
                if default_shift == att.shift:
                    if wh > 0 :
                        if wh < 24.0:
                            time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                            frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours', str(time_in_standard_format))
                            frappe.db.set_value('Attendance', att.name, 'working_hours', str(wh))
                        else:
                            wh = 24.0
                            frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours',"23:59:59")
                            frappe.db.set_value('Attendance', att.name, 'working_hours',wh)
                        if wh < 4.0:
                            if att.leave_application:
                                frappe.db.set_value('Attendance',att.name,'status','Half Day')
                            else:
                                frappe.db.set_value('Attendance',att.name,'status','Absent')
                        if wh>=4.0 and wh < 8.0:
                            frappe.db.set_value('Attendance',att.name,'status','Half Day')
                        elif wh>=8.0:
                            frappe.db.set_value('Attendance',att.name,'status','Present')
                    else:
                        frappe.db.set_value('Attendance',att.name,'custom_total_working_hours',"00:00:00")
                        frappe.db.set_value('Attendance',att.name,'working_hours',"0.0")
                else:
                    if wh > 0 :
                        if wh < 24.0:
                            time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                            frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours', str(time_in_standard_format))
                            frappe.db.set_value('Attendance', att.name, 'working_hours', wh)
                        else:
                            wh = 24.0
                            frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours',"23:59:59")
                            frappe.db.set_value('Attendance', att.name, 'working_hours',wh)
                        if wh < 4.0:
                            if att.leave_application:
                                frappe.db.set_value('Attendance',att.name,'status','Half Day')
                            else:
                                frappe.db.set_value('Attendance',att.name,'status','Absent')
                        if wh>=4.0 and wh < 8.0:
                            frappe.db.set_value('Attendance',att.name,'status','Half Day')
                        elif wh>=8.0:
                            frappe.db.set_value('Attendance',att.name,'status','Present')
                        else:
                                frappe.db.set_value('Attendance',att.name,'custom_total_working_hours',"00:00:00")
                                frappe.db.set_value('Attendance',att.name,'working_hours',"0.0")
            else:
                if wh > 0 :
                    if wh < 24.0:   
                        time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
                        frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours', str(time_in_standard_format))
                        frappe.db.set_value('Attendance', att.name, 'working_hours', wh)
                    else:
                        wh = 24.0
                        frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours',"23:59:59")
                        frappe.db.set_value('Attendance', att.name, 'working_hours',wh)
                    if wh < 4.0:
                        if att.leave_application:
                            frappe.db.set_value('Attendance',att.name,'status','Half Day')
                        else:
                            frappe.db.set_value('Attendance',att.name,'status','Absent')
                    if wh>=4.0 and wh < 8.0:
                        frappe.db.set_value('Attendance',att.name,'status','Half Day')
                    elif wh>=8.0:
                        frappe.db.set_value('Attendance',att.name,'status','Present')
                    else:
                        frappe.db.set_value('Attendance',att.name,'custom_total_working_hours',"00:00:00")
                        frappe.db.set_value('Attendance',att.name,'working_hours',"0.0")
        
def ot_calculation(from_date,to_date):
    attendance = frappe.db.sql("""select * from `tabAttendance` where attendance_date between '%s' and '%s' """%(from_date,to_date),as_dict=True)
    for att in attendance:
        if att.shift and att.out_time and att.in_time :
            shift_et = frappe.db.get_value("Shift Type",{'name':att.shift},['end_time'])
            out_time = datetime.strptime(str(att.out_time),'%Y-%m-%d %H:%M:%S').time()
            shift_et = datetime.strptime(str(shift_et), '%H:%M:%S').time()
            if shift_et < out_time:
                difference = time_diff_in_timedelta_1(shift_et,out_time)
                diff_time = datetime.strptime(str(difference), '%H:%M:%S').time()
                frappe.db.set_value("Attendance",att.name,"custom_ot_hours",diff_time)                  
                    

def time_diff_in_timedelta_1(time1, time2):
    datetime1 = datetime.combine(datetime.min, time1)
    datetime2 = datetime.combine(datetime.min, time2)
    timedelta_seconds = (datetime2 - datetime1).total_seconds()
    diff_timedelta = timedelta(seconds=timedelta_seconds)
    return diff_timedelta

def time_diff_in_timedelta(in_time, out_time):
    datetime_format = "%H:%M:%S"
    if out_time and in_time :
        return out_time - in_time
  
@frappe.whitelist()
def mark_late_entry(from_date,to_date):
    attendance = frappe.db.get_all('Attendance',{'attendance_date':('between',(from_date,to_date)),'docstatus':('!=','2')},['*'])
    for att in attendance:
        hh = check_holiday(att.attendance_date,att.employee)
        if not hh:
            night_shift=frappe.db.get_value("Shift Type",{"name": att.shift},["custom_is_night_shift"])
            if att.shift and att.in_time:
                in_time_date = att.in_time.date()
                if in_time_date==att.attendance_date:
                    shift_time = frappe.get_value(
                            "Shift Type", {'name': att.shift}, ["start_time"])
                    shift_start_time = datetime.strptime(
                        str(shift_time), '%H:%M:%S').time()
                    start_time = dt.datetime.combine(att.attendance_date,shift_start_time)
                    if att.in_time > datetime.combine(att.attendance_date, shift_start_time):
                        if att.in_time - start_time > timedelta(minutes=1):
                            frappe.db.set_value('Attendance', att.name, 'late_entry', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', att.in_time - start_time)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                    else:
                        frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                        frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                elif night_shift==1:
                    shift_data = frappe.get_value("Shift Type", {'name': att.shift}, ["start_time", "end_time"])
                    shift_start_time = datetime.strptime(str(shift_data[0]), '%H:%M:%S').time()
                    shift_end_time = datetime.strptime(str(shift_data[1]), '%H:%M:%S').time()
                    shift_date = att.attendance_date
                    start_time = dt.datetime.combine(shift_date, shift_start_time)
                    in_time = dt.datetime.combine(att.attendance_date, att.in_time.time())
                    if in_time < start_time and shift_start_time > shift_end_time:
                        in_time = add_days(in_time, 1)
                    if in_time > start_time and att.in_time.date() == add_days(shift_date,1):
                        late_time = in_time - start_time
                        if late_time > timedelta(minutes=1):
                            frappe.db.set_value('Attendance', att.name, 'late_entry', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', str(late_time))
                        else:
                            att.late_entry=0
                            att.custom_late_entry_time="00:00:00"
                            frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                    else:
                        frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                        frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
                else:
                    frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
                    frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
       
@frappe.whitelist()
def mark_early_out(from_date,to_date):
    attendance = frappe.db.get_all('Attendance',{'attendance_date':('between',(from_date,to_date)),'docstatus':('!=','2')},['*'])
    for att in attendance:  
        hh = check_holiday(att.attendance_date, att.employee)
        if not hh:
            night_shift=frappe.db.get_value("Shift Type",{"name": att.shift},["custom_is_night_shift"])
            if att.shift and att.out_time:
                out_time_date = att.out_time.date()
                if out_time_date==att.attendance_date and not night_shift==1:
                    shift_time = frappe.get_value(
                            "Shift Type", {'name': att.shift}, ["end_time"])
                    shift_end_time = datetime.strptime(
                        str(shift_time), '%H:%M:%S').time()
                    end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
                    if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
                        print(end_time - att.out_time )
                        if end_time - att.out_time > timedelta(minutes=1):
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_exit_time', end_time - att.out_time)
                        else:
                            frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                            frappe.db.set_value('Attendance', att.name, 'custom_early_exit_time', "00:00:00")
                    else:
                        frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                        frappe.db.set_value('Attendance', att.name, 'custom_early_exit_time', "00:00:00")

                elif night_shift == 1:
                    shift_time = frappe.get_value("Shift Type", {'name': att.shift}, ["end_time"])
                    shift_end_time = datetime.strptime(str(shift_time), '%H:%M:%S').time()

                    shift_end_datetime = datetime.combine(att.attendance_date, shift_end_time)
                    if shift_end_time < datetime.strptime("12:00:00", "%H:%M:%S").time():
                        shift_end_datetime += timedelta(days=1)

                    if att.out_time < shift_end_datetime:
                        early_out_duration = shift_end_datetime - att.out_time
                        frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
                        frappe.db.set_value('Attendance', att.name, 'custom_early_exit_time', early_out_duration)
                    else:
                        frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                        frappe.db.set_value('Attendance', att.name, 'custom_early_exit_time', "00:00:00")
                else:
                    frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
                    frappe.db.set_value('Attendance', att.name, 'custom_early_exit_time', "00:00:00")


                            

@frappe.whitelist()
def check_holiday(date, emp):

    holiday_list = frappe.db.get_value('Employee', {'name': emp}, 'holiday_list')
    holiday = frappe.db.sql("""SELECT `tabHoliday`.holiday_date, `tabHoliday`.weekly_off
                             FROM `tabHoliday List`
                             LEFT JOIN `tabHoliday` ON `tabHoliday`.parent = `tabHoliday List`.name
                             WHERE `tabHoliday List`.name = %s AND holiday_date = %s""",
                            (holiday_list, date), as_dict=True)
    doj = frappe.db.get_value("Employee", {'name': emp}, "date_of_joining")
    status = ''
    if holiday:
      
        if doj < holiday[0].holiday_date:
            if holiday[0].weekly_off == 1:
                
                status = "WW"
            else:
                status = "NH"
        else:
            status = 'Not Joined'
    return status

@frappe.whitelist()
def mark_att_test(date):
    from_date=date
    to_date=date
    mark_late_entry(from_date,to_date)
    mark_early_out(from_date,to_date)

#Create OT Request check with below conditions
@frappe.whitelist()
def update_ot_request(from_date,to_date):
    attendance = frappe.get_all("Attendance", {"attendance_date":("between",(from_date,to_date))}, ["*"])
    for i in attendance:
        doc = frappe.get_doc("Attendance",i.name)
        date = doc.attendance_date
        hh= check_holiday(date,doc.employee)
        applicable = frappe.db.get_value("Employee",{"name":doc.employee},["custom_ot_applicable"])
        if applicable ==1:
            if doc.shift and doc.in_time and doc.out_time:
                if doc.status == "Half Day" or doc.status == "Present":
                    if isinstance(doc.custom_ot_hours, str):
                        custom_ot_hours = datetime.strptime(doc.custom_ot_hours, '%H:%M:%S')
                        ot_timedelta = timedelta(hours=custom_ot_hours.hour, minutes=custom_ot_hours.minute, seconds=custom_ot_hours.second)
                    else:
                        ot_timedelta = doc.custom_ot_hours
                    if ot_timedelta and ot_timedelta > timedelta(hours=0, minutes=0, seconds=0):
                        if not frappe.db.exists("Over Time Request", {'employee': doc.employee, 'ot_date': date}):
                            req = frappe.new_doc("Over Time Request")
                            req.employee = doc.employee
                            req.ot_date = date
                            req.ot_hour = doc.custom_ot_hours
                            req.planned_hour = time(0, 0, 0)
                            req.shift = doc.shift
                            req.save(ignore_permissions=True)
                            frappe.db.commit()
                        else:
                            value =frappe.db.get_value("Over Time Request", {'employee': doc.employee, 'ot_date': date,"docstatus":("!=",2)},["name"])
                            document = frappe.get_doc("Over Time Request",value)
                            document.ot_hour = doc.custom_ot_hours
                            document.save(ignore_permissions=True)
                            frappe.db.commit()
                        

@frappe.whitelist()
def mark_attendance_from_checkin(employee,time,log_type):
    att_date = time.date()
    att_time = time.time()
    shift = ''
    if log_type == 'IN' and datetime.strptime('07:30:00', '%H:%M:%S').time() < att_time < datetime.strptime('15:30:00', '%H:%M:%S').time():
        checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'IN' and date(time) = '%s' and time(time) between "07:30:00" and "15:30:00" order by time ASC"""%(employee,att_date),as_dict=True)
        shift1 = frappe.db.get_value('Shift Type',{'name':'Morning shift'},['custom_checkin_start_time','custom_checkin_end_time'])
        shift_assignment = frappe.db.get_value("Shift Assignment",{"employee":employee,"start_date":att_date},["shift_type"])
        shift_start_time = frappe.db.get_value('Shift Type',{'name':shift_assignment},['start_time'])
        value = frappe.db.get_value("Special Occasion",{"date":att_date},["shift"])
        if (datetime.min + shift1[0]).time() < checkins[0].time.time() < (datetime.min + shift1[1]).time():
            if value==None:
                shift ='Morning shift'
        elif value:     
            shift = value
        elif shift_assignment and shift_start_time:
            shift_start_time = datetime.min + shift_start_time  # Assuming `start_time` is timedelta
            if shift_start_time.time() < checkins[0].time.time():
                shift = shift_assignment
        else:
            shift = ''
        att = frappe.db.exists('Attendance',{"employee":employee,'attendance_date':att_date,'docstatus':['!=','2']})   
        print(value)
        checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'IN' and date(time) = '%s' and time(time) between "07:30:00" and "15:30:00" order by time ASC"""%(employee,att_date),as_dict=True)
        if not att and checkins:
            shift_assignment = frappe.db.get_value("Shift Assignment",{"employee":employee,"start_date":att_date},["shift_type"])
            att = frappe.new_doc("Attendance")
            att.employee = employee
            att.attendance_date = att_date
            att.shift = shift
            att.custom_assigned_shift = shift_assignment
            att.status = 'Absent'
            att.in_time = checkins[0].time
            att.custom_late_entry_time = "00:00:00"
            att.custom_early_exit_time = "00:00:00"
            att.custom_total_working_hours="00:00:00"
            att.custom_ot_hours="00:00:00"
            att.working_hours = "0.0"
            att.save(ignore_permissions=True)
            frappe.db.commit()
            for c in checkins:
                frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
        else:
            shift_assignment = frappe.db.get_value("Shift Assignment",{"employee":employee,"start_date":att_date},["shift_type"])
            att = frappe.get_doc("Attendance",att)
            print(att.name)
            if att.docstatus == 0:
                att.employee = employee
                att.attendance_date = att_date
                att.shift = shift
                att.custom_assigned_shift = shift_assignment
                att.in_time = checkins[0].time
                att.working_hours = "0.0"
                att.custom_total_working_hours="00:00:00"
                att.custom_ot_hours="00:00:00"
                att.save(ignore_permissions=True)
                frappe.db.commit()
                for c in checkins:
                    print(c.name)
                    frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                    frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                return att 
    if log_type == 'OUT':
        max_out = datetime.strptime('10:30','%H:%M').time()
        in_time = frappe.db.get_value("Attendance",{"employee":employee,"attendance_date":att_date},["in_time"])
        if att_time < max_out:
            if in_time and in_time.time() < max_out and att_time > in_time.time():
                checkins = frappe.db.sql("select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'OUT' and date(time) = '%s' and time(time)<'%s' order by time ASC "%(employee,att_date,max_out),as_dict=True)
                att = frappe.db.exists("Attendance",{'employee':employee,'attendance_date':att_date})
                if att:
                    att = frappe.get_doc("Attendance",att)
                    if att.docstatus == 0:
                        if not att.shift:
                            if len(checkins) > 0:
                                att.shift = get_actual_shift(get_time(checkins[-1].time),employee,att_date)
                                att.out_time = checkins[-1].time
                                for c in checkins:
                                    frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                                    frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                            else:
                                if not att.shift:
                                    att.shift = get_actual_shift(get_time(checkins[-1].time),employee,att_date)
                                    att.out_time = checkins[0].time
                                frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
                                frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
                        else:
                            if len(checkins) > 0:
                                att.out_time = checkins[-1].time
                                for c in checkins:
                                    frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                                    frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                            else:
                                att.out_time = checkins[0].time
                                frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
                                frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
                        att.save(ignore_permissions=True)
                        frappe.db.commit()
                else:
                    shift_assignment = frappe.db.get_value("Shift Assignment",{"employee":employee,"start_date":att_date},["shift_type"])
                    att = frappe.new_doc("Attendance")
                    att.employee = employee
                    att.attendance_date = att_date
                    att.shift = shift
                    att.custom_assigned_shift = shift_assignment
                    att.status = 'Absent'
                    att.custom_ot_hours = "00:00:00"
                    if len(checkins) > 0:
                        if not att.shift:
                            att.shift = get_actual_shift(get_time(checkins[-1].time),employee,att_date)
                        att.out_time = checkins[-1].time
                        for c in checkins:
                            frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                            frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                    else:
                        if not att.shift:
                            att.shift = get_actual_shift(get_time(checkins[-1].time),att_date)
                        att.out_time = checkins[0].time
                        frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
                        frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
                    att.save(ignore_permissions=True)
                    frappe.db.commit()
        else:
            checkins = frappe.db.sql("select * from `tabEmployee Checkin` where employee ='%s' and log_type = 'OUT' and date(time) = '%s' and time(time)>'%s' order by time ASC"%(employee,att_date,max_out),as_dict=True)
            att = frappe.db.exists("Attendance",{'employee':employee,'attendance_date':att_date,'docstatus':("!=",2)})
            if att:
                att = frappe.get_doc("Attendance",att)
                if att.docstatus == 0:
                    if not att.shift:
                        if len(checkins) > 0:
                            if not att.shift:
                                att.shift = get_actual_shift(get_time(checkins[-1].time),employee,att_date)
                                att.out_time = checkins[-1].time
                            for c in checkins:
                                frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                                frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                        else:
                            if not att.shift:
                                att.shift = get_actual_shift(get_time(checkins[-1].time),employee,att_date)
                                att.out_time = checkins[0].time
                            frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
                            frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
                    else:
                        if len(checkins) > 0:
                            att.out_time = checkins[-1].time
                            for c in checkins:
                                frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                                frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                        else:
                            att.out_time = checkins[0].time
                            frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
                            frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
                    att.save(ignore_permissions=True)
                    frappe.db.commit()
            else:
                shift_assignment = frappe.db.get_value("Shift Assignment",{"employee":employee,"start_date":att_date},["shift_type"])
                att = frappe.new_doc("Attendance")
                att.employee = employee
                att.attendance_date = att_date
                att.shift = shift
                att.custom_assigned_shift = shift_assignment
                att.status = 'Absent'
                if len(checkins) > 0:
                    if not att.shift:
                        att.shift = get_actual_shift(get_time(checkins[-1].time),employee,att_date)
                    att.out_time = checkins[-1].time
                    for c in checkins:
                        frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
                        frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
                else:
                    if not att.shift:
                        att.shift = get_actual_shift(get_time(checkins[-1].time),att_date)
                    att.out_time = checkins[0].time
                    frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
                    frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
                att.save(ignore_permissions=True)
                frappe.db.commit()