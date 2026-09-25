# Copyright (c) 2025, Teampro and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe,erpnext

class ScrapModule(Document):
	def on_submit(self):
		entry = frappe.new_doc("Stock Entry")
		entry.stock_entry_type = "Material Issue"
		entry.batch_no = self.batch
		entry.append("items", {
			"item_code": self.item_code,
			"qty": self.qty,
			"s_warehouse": self.warehouse,
			"custom_scrap_module": self.name
		})
		entry.insert()
		entry.submit()
