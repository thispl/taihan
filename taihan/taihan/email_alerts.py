import frappe
from email.utils import formatdate
import frappe
import json
from frappe import _
from typing import Dict, Optional, Tuple, Union
from frappe.utils import time_diff, money_in_words
from frappe.utils.data import cstr
from frappe.utils import date_diff, add_months, today, add_days, nowdate, flt, getdate
import calendar
from frappe.utils.file_manager import get_file
from datetime import date, datetime, timedelta
from frappe import _, get_file_items
from frappe.utils import get_weekday
from datetime import datetime
from frappe.model.mapper import get_mapped_doc
from datetime import date
from frappe.utils import flt, fmt_money
from frappe.utils import get_first_day, today, get_last_day, format_datetime, add_years, date_diff, add_days, getdate, cint, format_date, get_url_to_form
from frappe.utils import add_months, add_days, format_time, today, nowdate, getdate, format_date
from frappe.utils import (
    add_days,
    add_months,
    cint,
    date_diff,
    flt,
    get_first_day,
    get_last_day,
    fmt_money,

)
from frappe.utils import (
    add_days,
    ceil,
    cint,
    comma_and,
    flt,
    get_link_to_form,
    getdate,
    now_datetime,
    datetime,get_first_day,get_last_day,
    nowdate,
    today,
)


import requests

#if continuous leave is taken without any inforamtion for more than 1 day only by the employee and not by the HR User, HR Manager and HOD, mail will send to HR User, HR Manager and HOD
@frappe.whitelist()
def employee_absent_days():
    today = frappe.utils.today()
    days_count = frappe.utils.add_days(today, -1)

    roles = ["HR User", "HR Manager", "HOD"]  # roles that have no restriction
    employees = frappe.get_all(
        "Employee",
        filters={"user_id": ["in", frappe.get_all("Has Role", filters={"role": ["in", roles]}, pluck="parent")]},
        pluck="name"
    )

    absent = frappe.db.sql("""
        SELECT employee, COUNT(attendance_date) AS absent_count
        FROM `tabAttendance`
        WHERE status = "Absent" AND attendance_date BETWEEN %s AND %s AND docstatus != 2
        GROUP BY employee
        HAVING absent_count > 1
    """, (days_count, today), as_dict=True)

    for abs in absent:
        emp = abs["employee"]

        if emp in employees:
            continue

        leave_application = frappe.db.exists(
            "Leave Application",
            {
                "employee": emp,
                "from_date": ["<=", today],
                "to_date": [">=", days_count],
                "docstatus": ["<", 2]
            }
        )

        if not leave_application:
            recipient_users = frappe.db.get_list(
            "Has Role",
            filters={"role": ["in", roles], "parenttype": "User"},
            fields=["parent as user_name"]
            )
            
            recipients = []
            for user in recipient_users:
                email =frappe.get_value("User", {'name': user['user_name'], 'enabled': 1}, "email")
                if email and email not in recipients:
                    recipients.append(email)
            
            if recipients:
                subject = f"Continuous Leave Without Any Information - {emp}"
                message = f"""
                Dear HR/HOD,<br><br>
                {emp} has taken continuous leave without any leave application.
                """

                frappe.sendmail(
                    recipients=recipients,
                    subject=subject,
                    message=message
                )
         
# Monthly Legal Compliance expiry alert daily cron
@frappe.whitelist()
def monthly_expiry_doc():   
    current_date = nowdate()
    next_date = add_days(current_date, 30)
    docs = frappe.get_all("Legal Compliance Monitor", 
                          filters={'alert_date': ("<=", current_date), 
                                   'next_due': (">=", current_date)},
                          fields=['name', 'days_left', 'next_due', 'name_of_licence'])   

    recipients_docs_map = {}  # This dictionary will map recipients to the documents

    for i in docs:
        doc = frappe.get_doc("Legal Compliance Monitor", i.name)
        # For each recipient, append the document information
        for user in doc.alert_mails:
            recipient = user.user
            if recipient not in recipients_docs_map:
                recipients_docs_map[recipient] = []  # Initialize if not present
            recipients_docs_map[recipient].append(i)

    # Now, send an email for each recipient with their corresponding documents
    for recipient, recipient_docs in recipients_docs_map.items():
        # Create the document list table for this recipient
        documents = '''
        <table class="table table-bordered" border=1 style="border-width:2px; border-color:#000;">
            <tr>
                <td colspan="8" style=text-align:center><b>Legal Compliance Monitor List</b></td>
            </tr>
            <tr style="border: 2px solid black;">
                <td colspan="2" style="border: 2px solid black;"><b>Document ID</b></td>
                <td colspan="2" style="border: 2px solid black;"><b>Document Name</b></td>
                <td colspan="2" style="border: 2px solid black;"><b>Expiry Date</b></td>
                <td colspan="2" style="border: 2px solid black;"><b>Days Left</b></td>
            </tr>
        '''
        
        for doc_info in recipient_docs:
            documents += '''
            <tr style="border: 2px solid black;">
                <td colspan="2" style="border: 2px solid black;">{name}</td>
                <td colspan="2" style="border: 2px solid black;">{name_of_licence}</td>
                <td colspan="2" style="border: 2px solid black;">{next_due}</td>
                <td colspan="2" style="border: 2px solid black;">{days_left}</td>
            </tr>
            '''.format(name=doc_info.name, 
                       name_of_licence=doc_info.name_of_licence, 
                       next_due=doc_info.next_due, 
                       days_left=doc_info.days_left)
        
        documents += '</table>'

        # Send the email to this recipient
        frappe.sendmail(
            recipients=[recipient],
            subject="Legal Compliance Monitor Expiry Alert",
            message=f"""
                Dear Sir/Mam,<br><br>
                Kindly find the attached Legal Compliance Monitor List for Expiry Soon.<br><br>
                {documents}
                <br><br>
                Regards,<br>
                Your Company
            """
        )


@frappe.whitelist()
def policy_expiry_date():
    
    employee = frappe.db.get_all("Employee",
                                 {"status": "Active"},
                                 ["employee_name", "custom_policy_expiry_date", "custom_policy_number", "user_id"])
    
    for emp in employee:
        if emp["custom_policy_expiry_date"] and emp["user_id"]:
            day_diff = date_diff(emp["custom_policy_expiry_date"], today())
            
            if day_diff == 30:
                frappe.sendmail(
                recipients = emp["user_id"],
                subject = "Reminder: Your Insurance Policy is About to Expire",
                message = f"""
                    Dear {emp['employee_name']},<br><br>
                    We would like to inform you that your insurance policy (Policy No: {emp['custom_policy_number']}) 
                    is set to expire on {emp['custom_policy_expiry_date'].strftime('%B %d, %Y')}.<br><br>
                    Please take the necessary steps to renew your policy before the expiry date to ensure continued coverage.<br><br>
                    Regards,<br>
                    HR Team<br><br>
                    <i>This is an automated message. Please do not reply to this email.</i>
                """
            )
                
@frappe.whitelist()
def mail_for_policy_expiry_date():
    job = frappe.db.exists('Scheduled Job Type', 'policy_expiry_date')
    if not job:
        sjt = frappe.new_doc("Scheduled Job Type")
        sjt.update({
            "method": 'taihan.taihan.email_alerts.policy_expiry_date',
            "frequency": 'Cron',
            "cron_format":'0 8 * * *'
        })
        sjt.save(ignore_permissions=True)