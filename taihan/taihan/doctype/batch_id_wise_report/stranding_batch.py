
# Copyright (c) 2025, Teampro and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import cstr, add_days, date_diff, getdate, format_date
from frappe.utils.csvutils import UnicodeWriter, read_csv_content
from frappe.utils.file_manager import get_file
from frappe.utils.background_jobs import enqueue
from frappe import _

from datetime import date, timedelta, datetime, time
import openpyxl
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
from six import BytesIO
import math

@frappe.whitelist()
def stranding_download():
    filename = 'Stranding Batch ID Wise Report'
    build_xlsx_response(filename)


def make_xlsx(data, sheet_name=None, wb=None, column_widths=None):
    args = frappe.local.form_dict
    column_widths = column_widths or []
    if wb is None:
        wb = openpyxl.Workbook()
         
    ws = wb.active
    ws.column_dimensions['A'].width = 10
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 20 
    ws.column_dimensions['D'].width = 30
    ws.column_dimensions['E'].width = 30
    ws.column_dimensions['F'].width = 30
    ws.column_dimensions['G'].width = 30
    ws.column_dimensions['H'].width = 30
    ws.column_dimensions['I'].width = 30
    ws.column_dimensions['J'].width = 30
    ws.column_dimensions['K'].width = 30
    ws.column_dimensions['L'].width = 30
    ws.column_dimensions['M'].width = 30
    ws.column_dimensions['N'].width = 30
    ws.column_dimensions['O'].width = 30
    ws.column_dimensions['P'].width = 30
    ws.column_dimensions['Q'].width = 30
    ws.column_dimensions['R'].width = 30
    ws.column_dimensions['S'].width = 30 
    ws.column_dimensions['T'].width = 15
    ws.column_dimensions['U'].width = 15
    ws.column_dimensions['V'].width = 30
    ws.column_dimensions['W'].width = 30
    ws.column_dimensions['X'].width = 30
    ws.column_dimensions['Y'].width = 30
    ws.column_dimensions['Z'].width = 30

    # === Title Row ===
    ws.append(["BATCH ID WISE REPORT"] + [" "] * 25)

    # === Header Row ===
    ws.append([
        'S.No','Date', 'Shift', 'Line No', 'Production Incharge', 'Operator', 
        'Line Speed','Batch ID','Core OD','Bobbin No' , 'Customer','Sales Order','Customer PO Number','Design','LOT No','Set No',
        'Fiber Type','Fiber Count', 'Cable Type','Inner Layer 1','Inner Layer 2','Inner Layer 3','Phy Length','OTDR Length','Production Remark','Quality Remark'
    ])

    # === Data Rows ===
    data1 = get_data_stranding(args)
    for idx, row in enumerate(data1, start=1):
        row[0] = idx  # Insert serial number
        ws.append(row)
    
    # === Styling ===
    align_center = Alignment(horizontal='center', vertical='center')

    # --- Title Row (Row 1) ---
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=26)
    for cell in ws[1]:
        cell.font = Font(bold=True, size=20)
        cell.alignment = align_center

    # --- Header Row (Row 2) ---
    header_fill = PatternFill(start_color="002060", end_color="002060", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")  # White font
    for cell in ws[2]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = align_center

    # === Borders for all cells ===
    border_thin = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    for row in ws.iter_rows(min_row=1, max_row=len(data1) + 2, min_col=1, max_col=26):
        for cell in row:
            cell.border = border_thin

    # === Freeze Header Row ===
    ws.freeze_panes = "A3"   # Keeps row 1 & 2 visible when scrolling

    # === Save File ===
    xlsx_file = BytesIO()
    wb.save(xlsx_file)
    return xlsx_file


def build_xlsx_response(filename):
    xlsx_file = make_xlsx(filename)
    frappe.response['filename'] = filename + '.xlsx'
    frappe.response['filecontent'] = xlsx_file.getvalue()
    frappe.response['type'] = 'binary'


def get_data_stranding(args=None):
    data = []
    from_date = frappe.form_dict.get("from_date")
    to_date = frappe.form_dict.get("to_date")
    filters = {"docstatus": 1, "operation": "Stranding"}
    if from_date and to_date:
        filters["posting_date"] = ["between", [from_date, to_date]]
    job_card = frappe.get_all("Job Card", filters=filters, order_by='posting_date asc', fields=['*'])
    if from_date and to_date and not job_card:
        frappe.throw(_("No Job Cards found for the selected date range."))
    for i in job_card:
        frappe.errprint(i.operation)
        batch_date = frappe.db.get_value("Batch", {'name': i.custom_batch_no}, 'creation')
        fiber_type = frappe.db.get_value("Work Order", {'name': i.work_order}, 'custom_fiber_type')
        fiber_count = frappe.db.get_value("Work Order", {'name': i.work_order}, 'custom_fiber_count')
        sales_order = frappe.db.get_value("Work Order", {"name": i.work_order}, 'sales_order')
        customer_po = frappe.db.get_value("Work Order",{"name": i.work_order},"custom_customer_po_no")
        otdr = frappe.db.get_value("Quality Inspection", {'reference_name': i.name}, 'custom_otdr_lengthm')
        remarks = frappe.db.get_value("Quality Inspection", {'reference_name': i.name}, 'remarks')
        production_incharge = frappe.db.get_value("Employee",{'name':i.custom_production_incharge},'employee_name')
        operator_name = frappe.db.get_value("Employee",{'name':i.custom_operator},'employee_name')
        lot_no = i.custom_lot_no or ''
        cable_type = i.custom_cable_type or ''
        inner_layer = (i.custom_inner_layer or '').strip()
        inner_1 = inner_layer if '1' in inner_layer else 'Nil'
        inner_2 = inner_layer if '2' in inner_layer else 'Nil'
        inner_3 = inner_layer if '3' in inner_layer else 'Nil'

        data.append([
            '',  # S.No placeholder
            batch_date.strftime("%d-%m-%Y") if batch_date else '',
            i.custom_shift or '',
            i.workstation or '',
            production_incharge or '',
            operator_name or '',
            i.custom_line_speed or '',
            i.custom_batch_no or '',
            i.custom_core_od or '',
            i.custom_bobbin_no or '',
            i.custom_customer_name or '',
            sales_order or '',
            customer_po or '',
            i.custom_design or '',
            lot_no,
            i.custom_set_no or '',
            fiber_type or '',
            fiber_count or '',
            cable_type or '',
            inner_1,
            inner_2,
            inner_3,
            i.total_completed_qty or '',
            otdr or '',
            i.custom_remark or '',
            remarks or '',
        ])
    return data
