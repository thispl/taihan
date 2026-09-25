import frappe
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.drawing.image import Image
from six import BytesIO
from datetime import datetime
import os
@frappe.whitelist()
def download_test_report(docname):
    filename = "Stranding Multimode"
    xlsx_file = make_test_report_multimode_excel(docname)
    frappe.response['filename'] = filename + '.xlsx'
    frappe.response['filecontent'] = xlsx_file.getvalue()
    frappe.response['type'] = 'binary'


def make_test_report_multimode_excel(docname):
    doc = frappe.get_doc("Quality Inspection", docname)

    wb = Workbook()
    ws = wb.active
    ws.title = "OTDR Test Report - Multi Mode"

    # --- Styles ---
    border = Border(
        left=Side(border_style='thin'),
        right=Side(border_style='thin'),
        top=Side(border_style='thin'),
        bottom=Side(border_style='thin')
    )
    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    align_left = Alignment(horizontal="left", vertical="top", wrap_text=True)
    bold_font = Font(bold=True)

    ws.merge_cells("A1:C3")
    ws.merge_cells("D1:J2")
    ws.merge_cells("D3:J3")
    for row in ws["D1:J2"]:
        for cell in row:
            cell.border = border

    for row in ws["D3:J3"]:
        for cell in row:
            cell.border = border
    ws["D1"] = "TAIHAN KUWAIT FIBER OPTIC CABLE CO"
    ws["D1"].font = Font(size=14, bold=True)
    ws["D1"].alignment = align_center
    ws["D3"] = "OTDR Test Report - Multi Mode"
    ws["D3"].font = Font(size=11, bold=True)
    ws["D3"].alignment = align_center

    file_url = "/files/Taihan Kuwait logo1_page-0001 (1).jpg"
    file_path = frappe.get_site_path("public", file_url.lstrip("/"))
    try:
        if os.path.exists(file_path):
            img = Image(file_path)
            img.width, img.height = 100, 50
            ws.add_image(img, "B1")
        else:
            ws["B1"] = "LOGO"
    except:
        ws["B1"] = "LOGO"

    customer = frappe.db.get_value("Sales Order", {"name": doc.sales_order}, "customer")
    manu_date = frappe.db.get_value("Job Card", {"name": doc.reference_name}, "posting_date")

    ws.merge_cells("A4:B4"); ws["A4"] = "Customer:"; ws["A4"].alignment=align_left
    ws.merge_cells("C4:F4"); ws["C4"] = customer or ''
    ws.merge_cells("G4:H4"); ws["G4"] = "Fiber Count:"
    ws.merge_cells("I4:J4"); ws["I4"] = f"{doc.custom_fiber_count or ''}F";ws["I4"].alignment = align_left

    ws.merge_cells("A5:B5"); ws["A5"] = "Sales Order No:"
    ws.merge_cells("C5:D5"); ws["C5"] = doc.sales_order or ''
    ws.merge_cells("E5:E5"); ws["E5"] = "Mfg. Date:"
    ws.merge_cells("F5:F5"); ws["F5"] = frappe.utils.formatdate(manu_date) if manu_date else ''
    ws.merge_cells("G5:H5"); ws["G5"] = "SZ Core ID:"
    ws.merge_cells("I5:J5"); ws["I5"] = doc.custom_sz_core_id or ''

    ws.merge_cells("A6:B6"); ws["A6"] = f"OTDR No: {doc.custom_otdr_no or ''}"
    ws.merge_cells("C6:C6"); ws["C6"] = "Fiber Type:"
    ws.merge_cells("D6:D6"); ws["D6"] = doc.custom_fiber_type or ''
    ws.merge_cells("E6:E6"); ws["E6"] = "Shift:"
    ws.merge_cells("F6:F6"); ws["F6"] = doc.custom_shift or ''
    ws.merge_cells("G6:H6"); ws["G6"] = "Drum No:"
    ws.merge_cells("I6:J6"); ws["I6"] = doc.custom_drum_no or ''

    ws.merge_cells("A7:A8"); ws["A7"] = "IOR"; ws["A7"].alignment = align_center
    ws["B7"] = "850nm"; ws["B7"].alignment = align_center
    ws["C7"] = "1300nm"; ws["C7"].alignment = align_center
    ws["D7"] = "Core OD(mm):"
    ws.merge_cells("E7:F7"); ws["E7"] = doc.custom_core_odmm or '';ws["E7"].alignment=align_left
    ws["G7"] = "Prod. Length(M):"
    ws.merge_cells("G7:H7"); ws["I7"] = doc.custom_production_length or ''
    ws.merge_cells("I7:J7")

    ws["B8"] = doc.custom_ior__850_nm or ''
    ws["C8"] = doc.custom_ior__1300_nm or ''
    ws["D8"] = "FRP OD(mm):"; ws["D8"].font = bold_font
    ws.merge_cells("E8:F8"); ws["E8"] = doc.custom_frp_od or ''
    ws.merge_cells("G8:J8"); ws["G8"] = f"OTDR Length(M): {doc.custom_otdr_lengthm or ''}";ws["G8"].alignment=align_left
    # ws.merge_cells("A9:A11"); ws["A9"] = "Tube Colour"; ws["A9"].font = bold_font
    # ws.merge_cells("B9:B11"); ws["B9"] = "Fiber Colour"; ws["B9"].font = bold_font
    # ws.merge_cells("C9:D9"); ws["C9"] = "Attenuation dB/km"; ws["C9"].font = bold_font
    # ws.merge_cells("E9:E11"); ws["E9"] = "Tube Colour"; ws["E9"].font = bold_font
    # ws.merge_cells("F9:F11"); ws["F9"] = "Fiber Colour"; ws["F9"].font = bold_font
    # ws.merge_cells("G9:H9"); ws["G9"] = "Attenuation dB/km"; ws["G9"].font = bold_font
    ws["H8"].alignment = align_left
    # ws["C10"] = "850 nm"; ws["C10"].font = bold_font
    # ws["D10"] = "1300 nm"; ws["D10"].font = bold_font
    # ws["G10"] = "850 nm"; ws["G10"].font = bold_font
    # ws["H10"] = "1300 nm"; ws["H10"].font = bold_font

    # --- Table Headers (with S.No) ---
    ws.merge_cells("A9:A11"); ws["A9"] = "S.No"; ws["A9"].font = bold_font
    ws.merge_cells("B9:B11"); ws["B9"] = "Tube Colour"; ws["B9"].font = bold_font
    ws.merge_cells("C9:C11"); ws["C9"] = "Fiber Colour"; ws["C9"].font = bold_font
    ws.merge_cells("D9:E9"); ws["D9"] = "Attenuation dB/km"; ws["D9"].font = bold_font

    ws.merge_cells("F9:F11"); ws["F9"] = "S.No"; ws["F9"].font = bold_font
    ws.merge_cells("G9:G11"); ws["G9"] = "Tube Colour"; ws["G9"].font = bold_font
    ws.merge_cells("H9:H11"); ws["H9"] = "Fiber Colour"; ws["H9"].font = bold_font
    ws.merge_cells("I9:J9"); ws["I9"] = "Attenuation dB/km"; ws["I9"].font = bold_font

    ws["D10"] = "850 nm"; ws["E10"] = "1300 nm"
    ws["I10"] = "850 nm"; ws["J10"] = "1300 nm"

    from collections import defaultdict

    align_center = Alignment(horizontal="center", vertical="center")
    border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin")
    )
    bold_font = Font(bold=True)

    # from collections import defaultdict

    # grouped_rows = defaultdict(list)
    # for row in doc.custom_mm_stranding_attenuation:
    #     grouped_rows[row.tube_colour].append(row)

    # # Flatten all rows keeping tube info
    # all_rows = []
    # for tube in grouped_rows:
    #     for row in grouped_rows[tube]:
    #         all_rows.append((tube, row))

    # # Split into two parts of 48 fibers each
    # part1_rows = all_rows[:48]
    # part2_rows = all_rows[48:]

    # start_row = 12

    # # --- Part 1: LEFT table (A-D) ---
    # for j, (tube, lrow) in enumerate(part1_rows):
    #     row = start_row + j
    #     # Merge tube every 12 fibers
    #     if j % 12 == 0:
    #         ws.merge_cells(start_row=row, start_column=1, end_row=row+11, end_column=1)
    #         ws[f"A{row}"] = tube
    #         ws[f"A{row}"].alignment = align_center
    #         ws[f"A{row}"].font = bold_font

    #     ws[f"B{row}"] = getattr(lrow, "fiber_colour", "")
    #     ws[f"C{row}"] = getattr(lrow, "attenuation_at_850_nm", "")
    #     ws[f"D{row}"] = getattr(lrow, "attenuation_at_1300_nm", "")

    #     for col in "ABCD":
    #         ws[f"{col}{row}"].border = border
    #         ws[f"{col}{row}"].alignment = align_center

    # # --- Part 2: RIGHT table (E-H) ---
    # for j, (tube, rrow) in enumerate(part2_rows):
    #     row = start_row + j
    #     # Merge tube every 12 fibers
    #     if j % 12 == 0:
    #         ws.merge_cells(start_row=row, start_column=5, end_row=row+11, end_column=5)
    #         ws[f"E{row}"] = tube
    #         ws[f"E{row}"].alignment = align_center
    #         ws[f"E{row}"].font = bold_font

    #     ws[f"F{row}"] = getattr(rrow, "fiber_colour", "")
    #     ws[f"G{row}"] = getattr(rrow, "attenuation_at_850_nm", "")
    #     ws[f"H{row}"] = getattr(rrow, "attenuation_at_1300_nm", "")

    #     for col in "EFGH":
    #         ws[f"{col}{row}"].border = border
    #         ws[f"{col}{row}"].alignment = align_center

    # current_row = ws.max_row + 1



    

    from collections import defaultdict

    grouped_rows = defaultdict(list)
    for row in doc.custom_mm_stranding_attenuation:
        grouped_rows[row.tube_colour].append(row)

    # Flatten all rows keeping tube info
    all_rows = []
    for tube in grouped_rows:
        for row in grouped_rows[tube]:
            all_rows.append((tube, row))

    # --- Dynamically split into 2 halves ---
    total_fibers = len(all_rows)

    if total_fibers <= 12:
        part1_rows = all_rows      # all fibers go to left table
        part2_rows = []            # right table empty
    else:
        half = total_fibers // 2
        part1_rows = all_rows[:half]
        part2_rows = all_rows[half:]

    start_row = 12
    merge_block = 12  # always merge 12 fibers per tube

    # # --- Part 1: LEFT table (A-D) ---
    # for j, (tube, lrow) in enumerate(part1_rows):
    #     row = start_row + j
    #     if j % merge_block == 0:  # merge tube name for 12 rows
    #         merge_end = row + min(merge_block, len(part1_rows) - j) - 1
    #         ws.merge_cells(start_row=row, start_column=1, end_row=merge_end, end_column=1)
    #         ws[f"A{row}"] = tube
    #         ws[f"A{row}"].alignment = align_center
    #         ws[f"A{row}"].font = bold_font

    #     ws[f"B{row}"] = getattr(lrow, "fiber_colour", "")
    #     ws[f"C{row}"] = getattr(lrow, "attenuation_at_850_nm", "")
    #     ws[f"D{row}"] = getattr(lrow, "attenuation_at_1300_nm", "")

    #     for col in "ABCD":
    #         ws[f"{col}{row}"].border = border
    #         ws[f"{col}{row}"].alignment = align_center

    # # --- Part 2: RIGHT table (E-H) ---
    # for j, (tube, rrow) in enumerate(part2_rows):
    #     row = start_row + j
    #     if j % merge_block == 0:
    #         merge_end = row + min(merge_block, len(part2_rows) - j) - 1
    #         ws.merge_cells(start_row=row, start_column=5, end_row=merge_end, end_column=5)
    #         ws[f"E{row}"] = tube
    #         ws[f"E{row}"].alignment = align_center
    #         ws[f"E{row}"].font = bold_font

    #     ws[f"F{row}"] = getattr(rrow, "fiber_colour", "")
    #     ws[f"G{row}"] = getattr(rrow, "attenuation_at_850_nm", "")
    #     ws[f"H{row}"] = getattr(rrow, "attenuation_at_1300_nm", "")

    #     for col in "EFGH":
    #         ws[f"{col}{row}"].border = border
    #         ws[f"{col}{row}"].alignment = align_center

    # # --- Get the row after both parts ---
    # current_row = start_row + len(part1_rows)  

    # --- Left table (A–E) ---
    for j, (tube, lrow) in enumerate(part1_rows):
        row = start_row + j
        ws[f"A{row}"] = j + 1  # S.No
        if j % merge_block == 0:
            merge_end = row + min(merge_block, len(part1_rows) - j) - 1
            ws.merge_cells(start_row=row, start_column=2, end_row=merge_end, end_column=2)
            ws[f"B{row}"] = tube
            ws[f"B{row}"].alignment = align_center
        ws[f"C{row}"] = lrow.fiber_colour or ''
        ws[f"D{row}"] = lrow.attenuation_at_850_nm or ''
        ws[f"E{row}"] = lrow.attenuation_at_1300_nm or ''
        for col in "ABCDE":
            ws[f"{col}{row}"].border = border
            ws[f"{col}{row}"].alignment = align_center

    # --- Right table (F–J) ---
    for j, (tube, rrow) in enumerate(part2_rows):
        row = start_row + j
        ws[f"F{row}"] = j + 1 + len(part1_rows)  # Continue numbering
        if j % merge_block == 0:
            merge_end = row + min(merge_block, len(part2_rows) - j) - 1
            ws.merge_cells(start_row=row, start_column=7, end_row=merge_end, end_column=7)
            ws[f"G{row}"] = tube
            ws[f"G{row}"].alignment = align_center
        ws[f"H{row}"] = rrow.fiber_colour or ''
        ws[f"I{row}"] = rrow.attenuation_at_850_nm or ''
        ws[f"J{row}"] = rrow.attenuation_at_1300_nm or ''
        for col in "FGHIJ":
            ws[f"{col}{row}"].border = border
            ws[f"{col}{row}"].alignment = align_center
    current_row = start_row + len(part1_rows) 

    

    normal_font = Font(bold=False)
    bold_font = Font(bold=True)

    ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row+4, end_column=5)
    cell = ws.cell(row=current_row, column=1)
    cell.value = f"Remark :\n{doc.remarks or ''}"
    cell.font = normal_font  
    cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)

    ws.merge_cells(start_row=current_row+5, start_column=4, end_row=current_row+5, end_column=5)
    ws.merge_cells(start_row=current_row+5, start_column=1, end_row=current_row+5, end_column=3)
    cell1= ws.cell(row=current_row+5, column=1, value="Prod. Operator Name: ")
    ws.cell(row=current_row+5, column=4, value = ( doc.custom_operator or ''))
    ws.merge_cells(start_row=current_row, start_column=6, end_row=current_row, end_column=10)
    bold_font = Font(bold=True)

    cell = ws.cell(row=current_row, column=6, value="Visual Inspection")
    cell.font = bold_font
    cell1.font = bold_font
    
    ws.merge_cells(start_row=current_row+1, start_column=6, end_row=current_row+4, end_column=10)
    ws.cell(
        row=current_row+1,
        column=6,
        value=f"No. Of Filler: \n"
            f"Tube sequence:\n"
            f"WBT Width(mm): \n"
            f"Lay Length(mm):"
    )

 
    ws.merge_cells(start_row=current_row+5, start_column=7, end_row=current_row+5, end_column=10)
    ws.merge_cells(start_row=current_row+5, start_column=6, end_row=current_row+5, end_column=6)
    ws.cell(row=current_row+5, column=6, value="Shift Engg. Name: ")
    ws.cell(row=current_row+5, column=7, value= (doc.custom_production_shift_engineering_name or ''))
    
    ws.merge_cells(start_row=current_row+6, start_column=3, end_row=current_row+6, end_column=5)
    ws.merge_cells(start_row=current_row+6, start_column=1, end_row=current_row+6, end_column=2)
    ws.cell(row=current_row+6, column=1, value="Tested by: ")
    ws.cell(row=current_row+6, column=3, value=(doc.inspected_by or ''))
    
    ws.cell(row=current_row+6, column=6, value="Sign & Date: " + (frappe.utils.formatdate(frappe.utils.today(), 'dd-MM-YYYY')))

    ws.merge_cells(start_row=current_row+6, start_column=6, end_row=current_row+6, end_column=10)

    column_widths = {
    "E":15,"B":15,"C":8 ,"H":15,
    "D": 15,
    "G": 15,
    "J": 15,
    }
    for col, width in column_widths.items():
        ws.column_dimensions[col].width = width


    
    for row in ws.iter_rows(min_row=current_row, max_row=current_row+5, min_col=1, max_col=10):
        for cell in row:
            cell.border = border
    for row in ws["D1:H2"]:
        for cell in row:
            cell.border = border
    for row in ws.iter_rows(min_row=ws.max_row-8, max_row=ws.max_row, min_col=1, max_col=10):
        for cell in row:
            cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
            cell.border = border

    for row in ws.iter_rows(min_row=4, max_row=6, max_col=10):
        for cell in row:
            cell.border = border
            cell.alignment = align_left
    for row in ws.iter_rows(min_row=7, max_row=ws.max_row-7, max_col=10):
        for cell in row:
            cell.border = border
            cell.alignment = align_center
    for row in ws["D3:H3"]:
        for cell in row:
            cell.border = border
    for row in ws.iter_rows(min_row=7, max_row=8,min_col=7, max_col=7):
        for cell in row:
            cell.border = border
            cell.alignment = align_left
    for row in ws.iter_rows(min_row=7, max_row=8,min_col=5, max_col=6):
        for cell in row:
            cell.border = border
            cell.alignment = align_left
    xlsx_file = BytesIO()
    wb.save(xlsx_file)
    xlsx_file.seek(0)
    return xlsx_file

