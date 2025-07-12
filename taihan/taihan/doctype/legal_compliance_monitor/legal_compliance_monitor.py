# Copyright (c) 2025, Teampro and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class LegalComplianceMonitor(Document):
	def on_update(self):
		if self.sponsor_company :
			sponsor_company = frappe.get_doc("Sponsor Company",self.sponsor_company)
			if self.name_of_licence == 'Commercial Registration':
				sponsor_company.update({
					"cr_issue_date" : self.issue_date,
					"cr_expiry_date" : self.next_due
				})
			if self.name_of_licence == 'Computer Card':
				sponsor_company.update({
					"computer_card_issue_date" : self.issue_date,
					"computer_card_expiry_date" : self.next_due
				})
			if self.name_of_licence == 'Trade License':
				sponsor_company.update({
					"baldia_issue_date" : self.issue_date,
					"baldia_expiry_date" : self.next_due
				})
			sponsor_company.db_update()

from frappe.utils import date_diff, add_months, today, add_days, nowdate, flt, getdate
from frappe.utils import add_months, add_days, format_time, today, nowdate, getdate, format_date


# Update the days left in legal Compliance monitor daily cron
@frappe.whitelist()
def update_days_left():
    value = frappe.get_all("Legal Compliance Monitor",["next_due","name"])
    for i in value:
        if i.next_due:
            diff = date_diff(i.next_due, today())
            frappe.db.set_value("Legal Compliance Monitor",i.name,"days_left",diff)
            next_due_date = frappe.utils.getdate(i.next_due)
            current_date = frappe.utils.getdate(today())
            next_due_month = next_due_date.month
            next_due_year = next_due_date.year
            current_month = current_date.month
            current_year = current_date.year
            if next_due_month == current_month and next_due_year == current_year and diff>=0:
                frappe.db.set_value("Legal Compliance Monitor", i.name, "status", "Expiring")
                frappe.db.set_value("Legal Compliance Monitor", i.name, "today_status", "Expiring")
            elif diff < 0:
                frappe.db.set_value("Legal Compliance Monitor", i.name, "status", "Expired")
                frappe.db.set_value("Legal Compliance Monitor", i.name, "today_status", "Expired")
            else:
                frappe.db.set_value("Legal Compliance Monitor", i.name, "status", "Active")
                frappe.db.set_value("Legal Compliance Monitor", i.name, "today_status", "Active")
                


