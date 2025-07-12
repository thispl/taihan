# Copyright (c) 2025, Teampro and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

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
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on

class RejoiningForm(Document):
    def on_update(self):
        if self.workflow_state == "Rejected":
            if not self.remarks:
                frappe.db.sql("""
                    UPDATE `tabRejoining Form`
                    SET docstatus = 0 , workflow_state = 'Pending for HR Manager'
                    WHERE name = %s
                """,(self.name),as_dict=True)
                self.reload()
            else:
                if self.status=="Rejected":
                    frappe.db.sql("""
                        UPDATE `tabRejoining Form`
                        SET docstatus = 1 , workflow_state = 'Rejected'
                        WHERE name = %s
                    """,(self.name),as_dict=True)
                    subject = f"Rejoining Form Rejected - {self.employee_name}"
                    message = f"""
                    Dear {self.employee_name},<br><br>
                    Your Rejoining Form has been Rejected due to the reason {self.remarks}
                    """

                    frappe.sendmail(
                        recipients=["jenisha.p@groupteampro.com","sarath.v@groupteampro.com","abdulla.pi@groupteampro.com"],
                        subject=subject,
                        message=message
                    )

        # if self.workflow_state == "Cancelled":
        #     if not self.cancellation_remarks:
        #         frappe.db.sql("""
        #                 UPDATE `tabRejoining Form`
        #                 SET docstatus = 1 , workflow_state = 'Approved'
        #                 WHERE name = %s
        #             """,(self.name),as_dict=True)
        #         self.reload()
            
        #     else:
        #         frappe.db.sql("""
        #         UPDATE `tabRejoining Form`
        #         SET docstatus = 2, workflow_state = 'Cancelled'
        #         WHERE name = %s
        #     """, (self.name,))
        
    # def on_submit(self):
        
    #     from_date = self.start
    #     to_date=self.end
    #     rejoining_date=self.re_join
    #     # if self.nature_of_leave=="Annual Leave" and date_diff(frappe.utils.data.getdate(self.re_join),frappe.utils.data.getdate(self.end))>1:
    #     if self.workflow_state == "Approved":
    #         if self.nature_of_leave=="Annual Leave" or self.nature_of_leave=="Hajj Leave" or self.nature_of_leave=="Umrah Leave" and date_diff(frappe.utils.data.getdate(self.re_join),frappe.utils.data.getdate(self.end))>1:
    #             if not frappe.db.exists("Leave Extension", {"leave_application": self.leave_application,"docstatus":("!=",2)}):
    #                 leave_ext= frappe.new_doc("Leave Extension")
    #                 leave_ext.employee=self.emp_no
    #                 leave_ext.from_date=from_date
    #                 leave_ext.to_date=to_date
    #                 leave_ext.extension_from_date=add_days(to_date, 1)
    #                 leave_ext.extension_to_date=add_days(rejoining_date, -1)
    #                 leave_ext.leave_application=self.leave_application
    #                 leave_ext.reason=self.custom_reason
    #                 leave_ext.custom_rejoining=self.name
    #                 leave_ext.leave_type=self.nature_of_leave
    #                 difference = date_diff(add_days(rejoining_date, -1), add_days(to_date, 1))
    #                 if difference >= 0:
    #                     leave_ext.total_no_of_days = difference + 1
    #                 leave_ext.save(ignore_permissions=True)
    #                 leave_ext.submit()
    #                 frappe.db.commit()
    # def before_cancel(self):
    #     if not self.cancellation_remarks:
    #         frappe.db.sql("""
    #         UPDATE `tabRejoining Form`
    #         SET docstatus = 1, workflow_state = 'Approved',status='Completed'
    #         WHERE name = %s
    #     """, (self.name,))
    #         frappe.db.commit() 
    #         frappe.throw("Cancellation remarks are required before cancelling the document.")
        
    #     else:
    #         frappe.db.sql("""
    #         UPDATE `tabRejoining Form`
    #         SET docstatus = 2, workflow_state = 'Cancelled',status='Hold'
    #         WHERE name = %s
    #     """, (self.name,))
    #     frappe.db.commit() 
    # def on_cancel(self):
    #     if self.workflow_state == "Cancelled":
    #         if not self.cancellation_remarks:
    #             if self.status=="Completed":
    #                 frappe.db.sql("""
    #                     UPDATE `tabRejoining Form`
    #                     SET docstatus = 1 , workflow_state = 'Approved'
    #                     WHERE name = %s
    #                 """,(self.name),as_dict=True)
    #                 self.reload()
    #             else:
    #                 frappe.db.sql("""
    #                     UPDATE `tabRejoining Form`
    #                     SET docstatus = 1 , workflow_state = 'Rejected'
    #                     WHERE name = %s
    #                 """,(self.name),as_dict=True)
    #         else:
    #             frappe.db.sql("""
    #                     UPDATE `tabRejoining Form`
    #                     SET docstatus = 2 , workflow_state = 'Cancelled'
    #                     WHERE name = %s
    #                 """,(self.name),as_dict=True)

    #     leave_extension = frappe.get_all("Leave Extension",{"leave_application": self.leave_application, "custom_rejoining": self.name},["name"])
    #     if leave_extension:
    #         leave_ext_doc = frappe.get_doc("Leave Extension", leave_extension[0].name)
    #         leave_ext_doc.cancel()
    #         frappe.db.commit()  

@frappe.whitelist()
def rejoining_date(employee,rejoin):
        leave_salary= frappe.db.get_value('Leave Salary', {'employee_number':employee},["name"])
        rejoining = frappe.db.sql("""select name,rejoining_date from `tabLeave Salary` where employee_number = '%s' order by `creation` desc limit 1 """ %(employee),as_dict=True)
        for i in rejoining:
            ls = frappe.get_doc("Leave Salary",{'name':i.name})
            ls.rejoining_date = rejoin 
            ls.save(ignore_permissions=True)
            frappe.db.commit()

   
