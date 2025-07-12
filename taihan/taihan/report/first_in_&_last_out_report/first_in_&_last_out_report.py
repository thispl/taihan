# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from datetime import datetime, date, timedelta
import frappe
from frappe import _, msgprint
from frappe.utils import data, format_datetime, add_days,today

def execute(filters=None):	
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	columns = [ 
		_("Employee ID") + ":Data:120",
		_("Employee Name") + ":Data:200",
		_("Department") + ":Data:200",
		_("Employee Category") + ":Data:120",
		_("Shift") + ":Data:100",
		_("Shift Hours") + ":Data:200",
		_("IN Time") + ":Data:200",
		_("OUT Time") + ":Data:200",
		_("Total Working Hours") + ":Data:100",
		_("Additional Working Hours") + ":Data:100",
 		

	]
	return columns

def get_data(filters):
	data = []
	today = date.today()
	if filters.date:
		today = filters.date
	roles = frappe.get_roles(frappe.session.user)
	if 'HR User' in roles:
		if filters.employee and filters.department:
			employees = frappe.get_all('Employee',{'status':'Active','department':filters.department,'name':filters.employee},['name','employee_name','department','custom_employee_category'])
		elif filters.employee:
			employees = frappe.get_all('Employee',{'status':'Active','name':filters.employee},['name','employee_name','department','custom_employee_category'])
		elif filters.department:
			employees = frappe.get_all('Employee',{'status':'Active','department':filters.department},['name','employee_name','department','custom_employee_category'])
		else:
			employees = frappe.get_all('Employee',{'status':'Active'},['name','employee_name','department','custom_employee_category'])
	else:
		employees = frappe.get_all('Employee',{'status':'Active','user_id':frappe.session.user},['name','employee_name','department','designation','custom_employee_category'])
	frm = datetime.strptime(filters.from_date, '%Y-%m-%d')
	to = datetime.strptime(filters.to_date, '%Y-%m-%d')
	f = frm.date()
	t = to.date()
	delta = t - f
	for i in range(delta.days + 1):
		day = f + timedelta(days=i)
	
		for emp in employees:
			in_time = ''
			out_time = ''
			shift_type=''
			shift_time=''
			in_checkins = frappe.db.sql("""select time from `tabEmployee Checkin` where log_type = 'IN' and employee = '%s'and date(time) = '%s' """ % (emp.name,day),as_dict=True)
			shift_type=frappe.db.get_value('Shift Assignment',{'employee':emp.name,'start_date':filters.from_date},['shift_type']) or ''
			s_time=frappe.db.get_value('Shift Type',{'name':shift_type},['start_time','end_time'])
			if s_time:
				start_time=str(s_time[0])
				end_time=str(s_time[1])
				shift_time=start_time + " - " + end_time
			if in_checkins:
				in_time = in_checkins[0]['time']
				shift = frappe.db.get_value('Shift Type',{'name':shift_type},['custom_checkin_start_time','custom_checkin_end_time'])
				if shift_type == '2':
					if in_time.time() < datetime.strptime(str(shift[0]), '%H:%M:%S').time():
						out_checkins = frappe.db.sql("""SELECT time FROM `tabEmployee Checkin` 
														WHERE log_type = 'OUT' AND employee = '%s' 
														AND date(time) = '%s' """ % (emp.name, day), as_dict=True)
					else:
						new_day = (in_time + timedelta(days=1)).date()
						out_checkins = frappe.db.sql("""SELECT time FROM `tabEmployee Checkin` 
													WHERE log_type = 'OUT' AND employee = '%s' 
													AND date(time) = '%s' """ % (emp.name, new_day), as_dict=True)
				else:
					out_checkins = frappe.db.sql("""SELECT time FROM `tabEmployee Checkin` 
														WHERE log_type = 'OUT' AND employee = '%s' 
														AND date(time) = '%s' """ % (emp.name, day), as_dict=True)
				if out_checkins:
					out_time = out_checkins[-1]['time']
					if out_time.time() < datetime.strptime('12:00:00', '%H:%M:%S').time():
						pass
			working_hours=0
			additional_hours=0
			shift_hours=timedelta(hours=8,minutes=0,seconds=0)
			if in_time and out_time:
				working_hours=out_time-in_time	
				
				if working_hours > shift_hours:
					additional_hours=working_hours-shift_hours
				
				
			if in_time or out_time: 
				data.append([emp.name,emp.employee_name,emp.department,emp.custom_employee_category,shift_type,shift_time,format_datetime(in_time),format_datetime(out_time),working_hours or '',additional_hours or ''])
	return data

