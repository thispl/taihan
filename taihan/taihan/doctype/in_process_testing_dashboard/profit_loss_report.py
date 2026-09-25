import frappe
from frappe.utils import nowdate
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from six import BytesIO
from erpnext.setup.utils import get_exchange_rate
from frappe.utils import flt
# from forex_python.converter import CurrencyRates
from frappe.utils import flt, getdate, fmt_money
import requests
from openpyxl.styles import Border, Side, Font

exchange_rates = {}

@frappe.whitelist()
def download():
	filename = 'Exchange Currency - Gain / Loss'
	build_xlsx_response(filename)

def make_xlsx(data=None, sheet_name="Sheet1", wb=None, column_widths=None):
	if wb is None:
		wb = Workbook()

	ws = wb.active
	ws.title = sheet_name

	thin_border = Border(
		left=Side(style='thin'),
		right=Side(style='thin'),
		top=Side(style='thin'),
		bottom=Side(style='thin')
	)
	green_font = Font(color="00B050") 
	red_font = Font(color="FF0000")


	ws["A3"] = 'Exchange Currency - Gain / Loss'
	ws["A3"].font = Font(bold=True, size=14)
	ws["A3"].alignment = Alignment(horizontal="center", vertical="center")
	ws.merge_cells("A3:J3")
 
	ws.append([""])
 
	headers = ["Party", "Party Name", "Invoice no", "Billing Currency Name", 
			   "Billing Amount", "Payment Currency Name", "Payment Amount", "Payment Type", "Gain / Loss", "Status"]

	ws.append(headers)
	header_row = ws.max_row

	for col, header in enumerate(headers, start=1):
		cell = ws.cell(row=header_row, column=col, value=header)
		cell.font = Font(bold=True)
		cell.alignment = Alignment(horizontal="center")
		cell.border = thin_border

	column_widths = [10, 50, 20, 25, 15, 23, 18, 13, 15]
	for i, width in enumerate(column_widths, start=1):
		ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width
  
	sales_invoice = frappe.get_all("Sales Invoice", {"status": "Paid"}, ["name", "currency", "grand_total", "customer"])
	for si in sales_invoice:
		pe = frappe.db.sql("""
			select c.reference_doctype, c.reference_name, p.paid_to_account_currency, sum(c.allocated_amount) as allocated_amount, p.name, p.payment_type
			from `tabPayment Entry` p
			inner join `tabPayment Entry Reference` c on c.parent = p.name
			where c.reference_name = %s and p.paid_to_account_currency is not NULL and p.docstatus = 1
			group by c.reference_name
		""", (si.name,), as_dict=True)

		if pe:
			pe = pe[0]
			gain_loss = get_gain_loss(pe.paid_to_account_currency, pe.allocated_amount, si.currency, si.grand_total, pe.payment_type)
			status = get_status(gain_loss)
			row_data = ["Customer", si.customer, si.name, si.currency, fmt_money(round(si.grand_total, 2)), 
						pe.paid_to_account_currency, fmt_money(round(pe.allocated_amount, 2)), pe.payment_type, fmt_money(round(gain_loss, 2)), status]
		

		ws.append(row_data)
  
		last_row = ws.max_row
		for col in range(1, len(row_data) + 1): 
			cell = ws.cell(row=last_row, column=col)
			cell.border = thin_border
			if col in [5, 7, 9] and last_row != 5:
				cell.alignment = Alignment(horizontal="right")
				if col == 9:  
					if gain_loss > 0:
						cell.font = green_font
					elif gain_loss < 0:
						cell.font = red_font
			if col == 10:  
				if status == "Gain":
					cell.font = green_font
				elif status == "Loss":
					cell.font = red_font
   
	purchase_invoice = frappe.get_all("Purchase Invoice", {"status": "Paid"}, ["name", "currency", "grand_total", "supplier"])
	for pi in purchase_invoice:
		pe = frappe.db.sql("""
			select c.reference_doctype, c.reference_name, p.paid_to_account_currency, sum(c.allocated_amount) as allocated_amount, p.name, p.payment_type
			from `tabPayment Entry` p
			inner join `tabPayment Entry Reference` c on c.parent = p.name
			where c.reference_name = %s and p.paid_to_account_currency is not NULL and p.docstatus = 1
			group by c.reference_name
		""", (pi.name,), as_dict=True)

		if pe:
			pe = pe[0]
			gain_loss = get_gain_loss(pe.paid_to_account_currency, pe.allocated_amount, pi.currency, pi.grand_total, pe.payment_type)
			status = get_status(gain_loss)
			row_data = ["Supplier", pi.supplier, pi.name, pi.currency, fmt_money(round(pi.grand_total, 2)), 
						pe.paid_to_account_currency, fmt_money(round(pe.allocated_amount, 2)), pe.payment_type, fmt_money(round(gain_loss, 2)), status]
		

		ws.append(row_data)

	# for pe in payment_entry:
	# 	if pe.reference_doctype == "Sales Invoice":
	# 		si = frappe.get_doc("Sales Invoice", pe.reference_name)
	# 		gain_loss = get_gain_loss(pe.paid_to_account_currency, pe.allocated_amount, si.currency, si.grand_total, pe.payment_type)
	# 		# gain_loss = 0
	# 		status = get_status(gain_loss)
	# 		row_data = ["Customer", si.customer, si.name, si.currency, fmt_money(round(si.grand_total, 2)), pe.paid_to_account_currency, fmt_money(round(pe.allocated_amount, 2)), fmt_money(round(gain_loss, 2)), status]
	# 		ws.append(row_data)
	# 	elif pe.reference_doctype == "Purchase Invoice":
	# 		pi = frappe.get_doc("Purchase Invoice", pe.reference_name)
	# 		gain_loss = get_gain_loss(pe.paid_to_account_currency, pe.allocated_amount, pi.currency, pi.grand_total, pe.payment_type)
	# 		# gain_loss = 20
	# 		status = get_status(gain_loss)
	# 		row_data = ["Supplier", pi.supplier, pi.name, pi.currency, fmt_money(round(pi.grand_total, 2)), pe.paid_to_account_currency, fmt_money(round(pe.allocated_amount, 2)), fmt_money(round(gain_loss, 2)), status]
	# 		ws.append(row_data)
		last_row = ws.max_row
		for col in range(1, len(row_data) + 1): 
			cell = ws.cell(row=last_row, column=col)
			cell.border = thin_border
			if col in [5, 7, 9] and last_row != 5:
				cell.alignment = Alignment(horizontal="right")
				if col == 9:  
					if gain_loss > 0:
						cell.font = green_font
					elif gain_loss < 0:
						cell.font = red_font
			if col == 10:  
				if status == "Gain":
					cell.font = green_font
				elif status == "Loss":
					cell.font = red_font

	xlsx_file = BytesIO()
	wb.save(xlsx_file)
	return xlsx_file

def build_xlsx_response(filename):
	xlsx_file = make_xlsx()
	frappe.response['filename'] = filename + '.xlsx'
	frappe.response['filecontent'] = xlsx_file.getvalue()
	frappe.response['type'] = 'binary'

def fetch_exchange_rates():
	"""Fetch exchange rates once and store them globally."""
	global exchange_rates
	if not exchange_rates:
		url = "https://api.freecurrencyapi.com/v1/latest?apikey=fca_live_87Iqr6cHBRxY0xoi0NOqcMyR6Xlhlsaq2VZOFgKs"
		response = requests.get(url)
		exchange_rates = response.json().get("data", {})

@frappe.whitelist(allow_guest=True)
def get_gain_loss(payment_currency, amount, billed_currency, billed_amount, payment_type):
	exchange_rate = get_exchange_rate(payment_currency, billed_currency)
	converted_amount = round((amount * exchange_rate), 2)
	# source_rate = exchange_rates.get(payment_currency)
	# target_rate = exchange_rates.get(billed_currency)
	
	# if not source_rate or not target_rate:
	# 	return 0
	
	# converted_amount = round((amount / source_rate) * target_rate, 2)
	return (billed_amount - converted_amount) if payment_type == "Pay" else (converted_amount - billed_amount)


@frappe.whitelist()
def get_status(gain_loss):
	if gain_loss > 0:
		result = "Gain"
		
	if gain_loss < 0:
		result = "Loss"
	if gain_loss == 0:
		result = "-"
	return result	

@frappe.whitelist()
def test_check():
	import requests
	payment_currency = "USD"
	billed_currency = "INR"
	amount = 500
	payment_type = "Pay"
	billed_amount = 500
 
	url = f"https://api.freecurrencyapi.com/v1/latest?apikey=fca_live_87Iqr6cHBRxY0xoi0NOqcMyR6Xlhlsaq2VZOFgKs"

	response = requests.get(url)
	data = response.json()
	print(data)
	source_rate = data["data"].get(payment_currency)
	target_rate = data["data"].get(billed_currency)
	converted_amount = round((amount / source_rate) * target_rate, 2)
	print(converted_amount)
	if payment_type == "Pay":
		gain_loss = billed_amount - converted_amount
	else:
		gain_loss = converted_amount - billed_amount
	return gain_loss

@frappe.whitelist()
def check_er():
	payment_type = "Pay"
	billed_amount = 53200.000
	amount = 53200.000
	exchange_rate = get_exchange_rate("INR", "KWD")
	print(exchange_rate)
	converted_amount = round((amount * exchange_rate), 2)
	print(converted_amount)
	return (billed_amount - converted_amount) if payment_type == "Pay" else (converted_amount - billed_amount)





import frappe
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from io import BytesIO

@frappe.whitelist()
def export_delivery_report():

	wb = Workbook()
	ws = wb.active
	ws.title = "Delivery Details"

	# Title
	ws.merge_cells("A1:R1")
	ws["A1"] = "Delivery Details"
	ws["A1"].font = Font(size=18, bold=True)
	ws["A1"].alignment = Alignment(horizontal="center")
	thin_border = Border(
			left=Side(style="thin"),
			right=Side(style="thin"),
			top=Side(style="thin"),
			bottom=Side(style="thin")
		)

	headers = [
		"Date Of Packing",
		"SO or PO No.",
		"Customer Name",
		"Packing List No.",
		"Invoice No",
		"Cable Description",
		"Cable Drum No.",
		"Net Weight (Kg)",
		"Gross Weight (Kg)",
		"Drum Size (mm)",
		"Total Length",
		"PO Amount in (KD)",
		"Advance Payment",
		"Balance Amount in (KD)",
		"FAT Date",
		"Inspection By",
		"Dispatch Date",
		"Drum Received"
	]

	header_fill = PatternFill(
		start_color="8DB4E2",
		end_color="8DB4E2",
		fill_type="solid"
	)

	for col_num, header in enumerate(headers, start=1):
		cell = ws.cell(row=2, column=col_num)
		cell.value = header
		cell.font = Font(bold=True)
		cell.fill = header_fill
		cell.alignment = Alignment(horizontal="center")

	row = 3

	delivery_notes = frappe.get_all(
		"Delivery Note",
		fields=["name", "customer", "posting_date"]
	)

	for dn in delivery_notes:

		doc = frappe.get_doc("Delivery Note", dn.name)

		if not doc.custom_dn_packing_list:
			continue

		invoice_no = ""
		sales_order = ""

		if doc.items:
			invoice_no = doc.items[0].get("against_sales_invoice", "")
			sales_order = doc.items[0].get("against_sales_order", "")

		po_amount = 0
		if sales_order:
			po_amount = frappe.db.get_value(
				"Sales Order",
				sales_order,
				"grand_total"
			) or 0
		# Advance Payment against Sales Order
		
		advance_payment = 0
		balance_amount = 0

		if sales_order:
			advance_payment = frappe.db.get_value(
				"Sales Order",
				sales_order,
				"advance_paid"
			) or 0

		# Balance Amount
		balance_amount = float(po_amount) - float(advance_payment)

		for pack in doc.custom_dn_packing_list:

			ws.cell(row=row, column=1).value = doc.posting_date
			ws.cell(row=row, column=1).number_format = "DD-MM-YYYY"
			ws.cell(row=row, column=2).value = sales_order
			ws.cell(row=row, column=3).value = doc.customer
			ws.cell(row=row, column=4).value = doc.name
			ws.cell(row=row, column=5).value = invoice_no

			ws.cell(row=row, column=6).value = pack.get("description", "")
			ws.cell(row=row, column=7).value = pack.get("drum_no", "")
			ws.cell(row=row, column=8).value = pack.get("net_weightkg", "")
			ws.cell(row=row, column=9).value = pack.get("gross_weightkg", "")
			ws.cell(row=row, column=10).value = pack.get("drum_sizemm", "")
			ws.cell(row=row, column=11).value = pack.get("total_length_mtr", "")

			ws.cell(row=row, column=12).value = po_amount
			ws.cell(row=row, column=13).value = advance_payment
			ws.cell(row=row, column=14).value = balance_amount
			ws.cell(row=row, column=15).value = doc.custom_fat_date or ""
			ws.cell(row=row, column=16).value = doc.custom_inspected_by or ""
			ws.cell(row=row, column=17).value = doc.posting_date
			ws.cell(row=row, column=17).number_format = "DD-MM-YYYY"
			ws.cell(row=row, column=18).value = doc.custom_drum_received or ""

			for col in range(1, 19):  
				cell = ws.cell(row=row, column=col)
				cell.alignment = Alignment(horizontal="center", vertical="center")
				cell.border = thin_border

			row += 1

	# Column Width Adjustment
	column_widths = {
		"A": 15,
		"B": 18,
		"C": 35,
		"D": 20,
		"E": 18,
		"F": 30,
		"G": 18,
		"H": 15,
		"I": 15,
		"J": 15,
		"K": 15,
		"L": 18,
		"M": 18,
		"N": 20,
		"O": 15,
		"P": 18,
		"Q": 18,
		"R": 15
	}

	for col, width in column_widths.items():
		ws.column_dimensions[col].width = width

	output = BytesIO()
	wb.save(output)

	frappe.response["filename"] = "Delivery_Details.xlsx"
	frappe.response["filecontent"] = output.getvalue()
	frappe.response["type"] = "download"