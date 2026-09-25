# Copyright (c) 2025, Teampro and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import cstr, add_days, date_diff, getdate, format_date, flt
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

from taihan.taihan.job_card_partial import _get_batches_for_job_card


class BatchIDWiseReport(Document):
    pass


@frappe.whitelist()
def download():
    filename = 'Buffering Batch ID Wise Report'
    build_xlsx_response(filename)


def make_xlsx(data, sheet_name=None, wb=None, column_widths=None):
    args = frappe.local.form_dict
    column_widths = column_widths or []
    if wb is None:
        wb = openpyxl.Workbook()

    ws = wb.active
    ws.title = sheet_name or "Buffering Batch ID Wise Report"
    ws.column_dimensions['A'].width = 5
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 10
    ws.column_dimensions['D'].width = 20
    ws.column_dimensions['E'].width = 30
    ws.column_dimensions['F'].width = 30
    ws.column_dimensions['G'].width = 15
    ws.column_dimensions['H'].width = 30    # Customer
    ws.column_dimensions['I'].width = 30    # Sales Order
    ws.column_dimensions['J'].width = 20    # Customer PO Number
    ws.column_dimensions['K'].width = 20    # Design
    ws.column_dimensions['L'].width = 12    # LOT No
    ws.column_dimensions['M'].width = 15    # Batch ID
    ws.column_dimensions['N'].width = 10    # Compound
    ws.column_dimensions['O'].width = 12    # Jelly
    ws.column_dimensions['P'].width = 12    # Fiber Type
    ws.column_dimensions['Q'].width = 12    # Set No
    ws.column_dimensions['R'].width = 12    # Fiber Count
    ws.column_dimensions['S'].width = 15    # LT Color
    ws.column_dimensions['T'].width = 12    # Tube ID
    ws.column_dimensions['U'].width = 15    # Tube OD
    ws.column_dimensions['V'].width = 15    # Tube Thickness
    ws.column_dimensions['W'].width = 18    # Tube OD(Min)
    ws.column_dimensions['X'].width = 18    # Tube OD(Max)
    ws.column_dimensions['Y'].width = 15    # Tube Thickness(Min)
    ws.column_dimensions['Z'].width = 15    # Tube Thickness(Max)
    ws.column_dimensions['AA'].width = 18   # Concentricity
    ws.column_dimensions['AB'].width = 20   # Phy Length
    ws.column_dimensions['AC'].width = 15   # ODTR Length
    ws.column_dimensions['AD'].width = 20   # Production Remark
    ws.column_dimensions['AE'].width = 30   # Quality Remark

    # === Title Row ===
    ws.append(["BATCH ID WISE REPORT"] + [" "] * 30)

    # === Header Row ===
    ws.append([
        'S.No','Date', 'Shift', 'Line No', 'Production Incharge', 'Operator', 
        'Line Speed', 'Customer','Sales Order','Customer PO Number','Design','LOT No','Batch ID','Compound','Jelly',
        'Fiber Type','Set No','Fiber Count','LT Color', 'Tube ID','Tube OD',
        'Tube Thickness','Tube OD(Min)','Tube OD(Max)','Tube Thickness(Min)','Tube Thickness(Max)','Concentricity',
        'Phy Length','ODTR Length','Production Remark','Quality Remark'
    ])

    # === Data Rows ===
    data1 = get_data(args)
    for idx, row in enumerate(data1, start=1):
        row[0] = idx  # Insert serial number
        ws.append(row)
    
    # === Styling ===
    align_center = Alignment(horizontal='center', vertical='center')

    # --- Title Row (Row 1) ---
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=31)
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

    for row in ws.iter_rows(min_row=1, max_row=len(data1)+2,min_col=1,max_col=31):
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


def get_data(args=None):
    data = []
    from_date = frappe.form_dict.get("from_date")
    to_date = frappe.form_dict.get("to_date")
    filters = {"docstatus": 1, "operation": "Buffering"}
    if from_date and to_date:
        filters["posting_date"] = ["between", [from_date, to_date]]
    job_card = frappe.get_all("Job Card", filters=filters, order_by='posting_date asc', fields=['*'])
    if ( from_date and to_date ) and not job_card:
        frappe.throw(_("No Job Cards found for the selected date range."))
    for i in job_card:
        fiber_type = frappe.db.get_value("Work Order", {'name': i.work_order}, 'custom_fiber_type')
        fiber_count = frappe.db.get_value("Work Order", {'name': i.work_order}, 'custom_fiber_count')
        sales_order = frappe.db.get_value("Work Order", {"name": i.work_order}, 'sales_order')
        customer_po = frappe.db.get_value("Work Order",{"name": i.work_order},"custom_customer_po_no")
        actual_id = frappe.db.get_value("Quality Inspection", {'reference_name': i.name}, 'custom_lt_id')
        tube_id_min = frappe.db.get_value("Quality Inspection", {'reference_name': i.name}, 'custom_lt_od_min')
        tube_id_max = frappe.db.get_value("Quality Inspection", {'reference_name': i.name}, 'custom_lt_od_max')
        actual_thickness = frappe.db.get_value("Quality Inspection", {'reference_name': i.name}, 'custom_thickness_min')
        thick_max = frappe.db.get_value("Quality Inspection", {'reference_name': i.name}, 'custom_thickness_max')
        otdr = frappe.db.get_value("Quality Inspection", {'reference_name': i.name}, 'custom_otdr_lengthm')
        remarks = frappe.db.get_value("Quality Inspection", {'reference_name': i.name}, 'remarks')
        result = frappe.db.get_value("Quality Inspection", {'reference_name': i.name}, 'custom_kink_test')
        production_incharge = frappe.db.get_value("Employee",{'name':i.custom_production_incharge},'employee_name')
        operator_name = frappe.db.get_value("Employee",{'name':i.custom_operator},'employee_name')
        lot_no = i.custom_lot_no or ''

        batches = _get_batches_for_job_card(i.name)
        if not batches:
            batches = [{'batch_no': i.custom_batch_no or '', 'qty': flt(i.total_completed_qty)}]

        for b in batches:
            batch_date = frappe.db.get_value("Batch", {'name': b['batch_no']}, 'creation')
            data.append([
                '',  # S.No placeholder
                batch_date.strftime("%d-%m-%Y") if batch_date else '',
                i.custom_shift or '',
                i.workstation or '',
                production_incharge or '',
                operator_name or '',
                i.custom_line_speed or '',
                i.custom_customer_name or '',
                sales_order or '',
                customer_po or '',

                i.custom_design or '',
                lot_no,
                b['batch_no'] or '',
                i.custom_compound or '',
                i.custom_jelly or '',
                fiber_type or '',
                i.custom_set_no or '',
                fiber_count or '',
                i.custom_tube_color or '',
                i.custom_production_id or '',
                i.custom_production_od or '',
                i.custom_tube_thickness or '',
                tube_id_min or '',
                tube_id_max or '',
                actual_thickness or '',
                thick_max or '',
                '',
                b['qty'] or '',
                otdr or '',
                i.custom_remark or '',
                remarks or '',
            ])
    return data


@frappe.whitelist()
def download_tracking():
    filename = 'Batch ID Wise Tracking Report'
    build_tracking_xlsx_response(filename)


def build_tracking_xlsx_response(filename):
    jacketing_batch = cstr(frappe.form_dict.get('jacketing_batch'))
    xlsx_file = make_tracking_xlsx(jacketing_batch)
    frappe.response['filename'] = filename + '.xlsx'
    frappe.response['filecontent'] = xlsx_file.getvalue()
    frappe.response['type'] = 'binary'


def make_tracking_xlsx(jacketing_batch):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Batch ID Wise Tracking Report'
    ws.column_dimensions['A'].width = 8
    ws.column_dimensions['B'].width = 25
    ws.column_dimensions['C'].width = 20
    ws.column_dimensions['D'].width = 25
    ws.column_dimensions['E'].width = 25
    ws.column_dimensions['F'].width = 20
    ws.column_dimensions['G'].width = 20
    ws.column_dimensions['H'].width = 25
    ws.column_dimensions['I'].width = 25
    ws.column_dimensions['J'].width = 20
    ws.column_dimensions['K'].width = 20
    ws.column_dimensions['L'].width = 20

    ws.append(['BATCH ID WISE TRACKING REPORT'] + [' '] * 11)
    ws.append(['S.No','Production Plan','Jacketing Batch','Jacketing Work Order','Jacketing Job Card','Jacketing Total Qty','Operation','Work Order','Job Card','Batch ID','Total Completed Qty','Batch Date'])

    data = get_tracking_data(jacketing_batch)
    for idx, row in enumerate(data, start=1):
        row[0] = idx
        ws.append(row)

    align_center = Alignment(horizontal='center', vertical='center')
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=12)
    for cell in ws[1]:
        cell.font = Font(bold=True, size=20)
        cell.alignment = align_center

    header_fill = PatternFill(start_color='002060', end_color='002060', fill_type='solid')
    header_font = Font(bold=True, color='FFFFFF')
    for cell in ws[2]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = align_center

    border_thin = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
    for row in ws.iter_rows(min_row=1, max_row=len(data)+2, min_col=1, max_col=12):
        for cell in row:
            cell.border = border_thin

    ws.freeze_panes = 'A3'
    xlsx_file = BytesIO()
    wb.save(xlsx_file)
    return xlsx_file


def get_tracking_data(jacketing_batch):
    if not jacketing_batch:
        frappe.throw(_('Please enter a Jacketing Batch'))
    jc = frappe.get_all('Job Card', filters={'operation':'Jacketing','custom_batch_no':jacketing_batch,'docstatus':1}, fields=['name','work_order','custom_batch_no','total_completed_qty'], limit=1)
    if not jc:
        jc = frappe.get_all('Job Card', filters={'operation':'Jacketing','custom_all_batch_nos':['like','%' + jacketing_batch + '%'],'docstatus':1}, fields=['name','work_order','custom_batch_no','total_completed_qty'], limit=1)
    if not jc:
        frappe.throw(_('No Jacketing Job Card found for batch {0}').format(jacketing_batch))
    jc = jc[0]
    wo = jc.work_order
    pp = frappe.db.get_value('Work Order', wo, 'production_plan')
    if not pp:
        frappe.throw(_('No Production Plan linked to Jacketing Work Order {0}').format(wo))
    data = []
    wos = frappe.get_all('Work Order', filters={'production_plan':pp,'name':['!=',wo]}, fields=['name','custom_operation_name'])
    for w in wos:
        op = w.custom_operation_name or ''
        jcs = frappe.get_all('Job Card', filters={'work_order':w.name,'docstatus':1}, fields=['name','custom_batch_no','custom_all_batch_nos','total_completed_qty'], order_by='name')
        for j in jcs:
            batches = []
            if j.custom_all_batch_nos:
                batches = [b.strip() for b in j.custom_all_batch_nos.split(',') if b.strip()]
            if not batches and j.custom_batch_no:
                batches = [j.custom_batch_no]
            for b in batches:
                bd = frappe.db.get_value('Batch', {'name':b}, 'creation')
                bdate = bd.strftime('%d-%m-%Y') if bd else ''
                data.append(['', pp, jc.custom_batch_no or '', wo or '', jc.name or '', jc.total_completed_qty or '', op, w.name or '', j.name or '', b, j.total_completed_qty or '', bdate])
    return data



