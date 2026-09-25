import frappe
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.drawing.image import Image
from six import BytesIO
from datetime import datetime
import os
@frappe.whitelist()
def download_test_report(docname):
    filename = "Stranding Single Mode"
    xlsx_file = make_test_report(docname)
    frappe.response['filename'] = filename + '.xlsx'
    frappe.response['filecontent'] = xlsx_file.getvalue()
    frappe.response['type'] = 'binary'


def make_test_report(docname):
    doc = frappe.get_doc("Quality Inspection", docname)

    wb = Workbook()
    ws = wb.active
    ws.title = "OTDR Test Report"
    border = Border(
        left=Side(border_style='thin'),
        right=Side(border_style='thin'),
        top=Side(border_style='thin'),
        bottom=Side(border_style='thin')
    )
    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    align_left = Alignment(horizontal="left", vertical="center")
    for row in ws["D1:L2"]:
        for cell in row:
            cell.border = border

    for row in ws["D3:L3"]:
        for cell in row:
            cell.border = border
    ws.merge_cells("A1:C3")  
    ws.merge_cells("D1:L2")
    ws.merge_cells("D3:L3")
    ws["D3"].border=border
    ws["D1"] = "TAIHAN KUWAIT FIBER OPTIC CABLE CO"
    ws["D1"].font = Font(size=14, bold=True)
    ws["D1"].alignment = align_center
    ws["D3"] = "OTDR Test Report - Stranding Line"
    ws["D3"].font = Font(size=11, bold=True)
    file_url = "/files/Taihan Kuwait logo1_page-0001 (1).jpg"   
    file_path = frappe.get_site_path("public", file_url.lstrip("/"))
    ws["D3"].alignment = align_center
    try:
        if os.path.exists(file_path):
            img = Image(file_path)
            img.width, img.height = 100, 50
            ws.add_image(img, "B1")
        else:
            # Try fallback logo
            fallback_logo = frappe.get_site_path("public", "files", "logo.png")
            if os.path.exists(fallback_logo):
                img = Image(fallback_logo)
                img.width, img.height = 120, 60
                ws.add_image(img, "A1")
            else:
                ws["B1"] = "LOGO"
    except Exception as e:
        ws["B1"] = "LOGO"
    customer = frappe.db.get_value("Sales Order",{"name":doc.sales_order},"customer")
    ws.merge_cells("A4:B4"); ws["A4"] = "Customer:"
    ws.merge_cells("C4:G4"); ws["C4"] = customer or ''
    ws.merge_cells("H4:I4"); ws["H4"] = "Fiber Count"
    ws.merge_cells("J4:L4"); ws["J4"] = doc.custom_fiber_count or ''
    manu_date = frappe.db.get_value("Job Card",{"name":doc.reference_name},"posting_date")
    ws.merge_cells("A5:B5"); ws["A5"] = "Sales Order No:"
    ws.merge_cells("C5:D5");ws["C5"] = doc.sales_order or ''
    ws["E5"] = "Mfg Date :"
    ws.merge_cells("F5:G5");ws["F5"] = frappe.utils.formatdate(manu_date) if manu_date else ""
    ws["H5"] = "SZ Core ID:"
    ws.merge_cells("H5:I5"); ws["J5"] = doc.custom_sz_core_id or '' 
    ws.merge_cells("J5:L5")
    ws["F7"].alignment = align_left   # Core OD
    ws["H8"].alignment = align_left   # OTDR Length
    ws.merge_cells("A6:B6")
    ws["A6"] = "OTDR No:" + (doc.custom_otdr_no or '')
 
    ws.merge_cells("C6:C6"); ws["C6"] = "Fiber Type:"
    ws.merge_cells("D6:D6"); ws["D6"] = doc.custom_fiber_type or ''
    ws["E6"] = "Shift :"
    ws.merge_cells("F6:G6");ws["F6"] = doc.custom_shift or ''
    ws["H6"] = "Drum No:"
    ws.merge_cells("H6:I6");ws["J6"]= doc.custom_drum_no or ''
    ws.merge_cells("J6:L6")
    
    
    ws.merge_cells("A7:A8"); ws["A7"] = "IOR"
    ws["B7"] = "1310nm"
    ws["C7"] = "1550nm"
    ws["D7"] = "1625nm"
    ws["E7"] = "Core OD(mm):"
    ws.merge_cells("F7:G7");ws["F7"] = doc.custom_core_odmm or ''
    ws["H7"] = "Prod.Length (M):"
    ws.merge_cells("H7:I7");ws["J7"]= doc.custom_production_length or ''
    ws.merge_cells("J7:L7")

    ws["B8"] = doc.custom_ior__1310_nm or ""
    ws["C8"] = doc.custom_ior__1550_nm or ""
    ws["D8"] = doc.custom_ior__1625_nm or ""
    ws["E8"] = "FRP OD (mm):"
    ws.merge_cells("F8:G8");ws["F8"] = doc.custom_frp_od or ''
    bold_font = Font(bold=True)
    normal_font = Font(bold=False)
    ws.merge_cells("H8:L8")
    ws["H8"] = f"OTDR Length (M): {doc.custom_otdr_lengthm:.2f}" if doc.custom_otdr_lengthm else "OTDR Length (M):"
    # ws.merge_cells("A9:A11"); ws["A9"] = "Tube Colour"; ws["A9"].font = bold_font
    # ws.merge_cells("B9:B11"); ws["B9"] = "Fiber Colour"; ws["B9"].font = bold_font
    # ws.merge_cells("C9:E9"); ws["C9"] = "Attenuation dB/km"; ws["C9"].font = bold_font
    # ws.merge_cells("F9:F11"); ws["F9"] = "Tube Colour"; ws["F9"].font = bold_font
    # ws.merge_cells("G9:G11"); ws["G9"] = "Fiber Colour"; ws["G9"].font = bold_font
    # ws.merge_cells("H9:J9"); ws["H9"] = "Attenuation dB/km"; ws["H9"].font = bold_font
    ws["H8"].alignment = align_left
    # ws["C10"] = "1310 nm"; ws["C10"].font = bold_font
    # ws["D10"] = "1550 nm"; ws["D10"].font = bold_font
    # ws["E10"] = "1625 nm"; ws["E10"].font = bold_font
    # ws["H10"] = "1310 nm"; ws["H10"].font = bold_font
    # ws["I10"] = "1550 nm"; ws["I10"].font = bold_font
    # ws["J10"] = "1625 nm"; ws["J10"].font = bold_font

     # --- Headers for Left and Right Tables ---
    ws.merge_cells("A9:A11"); ws["A9"] = "S.No"; ws["A9"].font = bold_font
    ws.merge_cells("B9:B11"); ws["B9"] = "Tube Colour"; ws["B9"].font = bold_font
    ws.merge_cells("C9:C11"); ws["C9"] = "Fiber Colour"; ws["C9"].font = bold_font
    ws.merge_cells("D9:F9"); ws["D9"] = "Attenuation dB/km"; ws["D9"].font = bold_font

    ws.merge_cells("G9:G11"); ws["G9"] = "S.No"; ws["G9"].font = bold_font
    ws.merge_cells("H9:H11"); ws["H9"] = "Tube Colour"; ws["H9"].font = bold_font
    ws.merge_cells("I9:I11"); ws["I9"] = "Fiber Colour"; ws["I9"].font = bold_font
    ws.merge_cells("J9:L9"); ws["J9"] = "Attenuation dB/km"; ws["J9"].font = bold_font

    ws["D10"] = "1310 nm"; ws["E10"] = "1550 nm"; ws["F10"] = "1625 nm"
    ws["J10"] = "1310 nm"; ws["K10"] = "1550 nm"; ws["L10"] = "1625 nm"

    # from collections import defaultdict

    # grouped_rows = defaultdict(list)
    # for row in doc.custom_stranding_attenuation:
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

    # # --- Part 1: left table (A-E) ---
    # for j, (tube, lrow) in enumerate(part1_rows):
    #     row = start_row + j
    #     if j % 12 == 0:
    #         ws.merge_cells(start_row=row, start_column=1, end_row=row+11, end_column=1)
    #         ws[f"A{row}"] = tube
    #         ws[f"A{row}"].alignment = align_center

    #     ws[f"B{row}"] = lrow.fiber_colour if lrow else ""
    #     ws[f"C{row}"] = lrow.attenuation_at_1310_nm if lrow else ""
    #     ws[f"D{row}"] = lrow.attenuation_at_1550_nm if lrow else ""
    #     ws[f"E{row}"] = lrow.attenuation_at_1625_nm if lrow else ""

    #     for col in "ABCDE":
    #         ws[f"{col}{row}"].border = border
    #         ws[f"{col}{row}"].alignment = align_center

    # # --- Part 2: right table (F-J) ---
    # for j, (tube, rrow) in enumerate(part2_rows):
    #     row = start_row + j
    #     if j % 12 == 0:
    #         ws.merge_cells(start_row=row, start_column=6, end_row=row+11, end_column=6)
    #         ws[f"F{row}"] = tube
    #         ws[f"F{row}"].alignment = align_center

    #     ws[f"G{row}"] = rrow.fiber_colour if rrow else ""
    #     ws[f"H{row}"] = rrow.attenuation_at_1310_nm if rrow else ""
    #     ws[f"I{row}"] = rrow.attenuation_at_1550_nm if rrow else ""
    #     ws[f"J{row}"] = rrow.attenuation_at_1625_nm if rrow else ""

    #     for col in "FGHIJ":
    #         ws[f"{col}{row}"].border = border
    #         ws[f"{col}{row}"].alignment = align_center




        

    from collections import defaultdict

    grouped_rows = defaultdict(list)
    for row in doc.custom_stranding_attenuation:
        grouped_rows[row.tube_colour].append(row)

    # Flatten all rows keeping tube info
    all_rows = []
    for tube in grouped_rows:
        for row in grouped_rows[tube]:
            all_rows.append((tube, row))

    total_fibers = len(all_rows)

    if total_fibers <= 12:
        part1_rows = all_rows
        part2_rows = []
    else:
        half = total_fibers // 2
        part1_rows = all_rows[:half]
        part2_rows = all_rows[half:]


    start_row = 12
    merge_block = 12   # 🔑 fixed 12 rows per tube

    # # --- Part 1: left table (A-E) ---
    # for j, (tube, lrow) in enumerate(part1_rows):
    #     row = start_row + j
    #     if j % merge_block == 0:
    #         merge_end = row + min(merge_block, len(part1_rows) - j) - 1
    #         ws.merge_cells(start_row=row, start_column=1, end_row=merge_end, end_column=1)
    #         ws[f"A{row}"] = tube
    #         ws[f"A{row}"].alignment = align_center

    #     ws[f"B{row}"] = lrow.fiber_colour if lrow else ""
    #     ws[f"C{row}"] = lrow.attenuation_at_1310_nm if lrow else ""
    #     ws[f"D{row}"] = lrow.attenuation_at_1550_nm if lrow else ""
    #     ws[f"E{row}"] = lrow.attenuation_at_1625_nm if lrow else ""

    #     for col in "ABCDE":
    #         ws[f"{col}{row}"].border = border
    #         ws[f"{col}{row}"].alignment = align_center

    # # --- Part 2: right table (F-J) ---
    # for j, (tube, rrow) in enumerate(part2_rows):
    #     row = start_row + j
    #     if j % merge_block == 0:
    #         merge_end = row + min(merge_block, len(part2_rows) - j) - 1
    #         ws.merge_cells(start_row=row, start_column=6, end_row=merge_end, end_column=6)
    #         ws[f"F{row}"] = tube
    #         ws[f"F{row}"].alignment = align_center

    #     ws[f"G{row}"] = rrow.fiber_colour if rrow else ""
    #     ws[f"H{row}"] = rrow.attenuation_at_1310_nm if rrow else ""
    #     ws[f"I{row}"] = rrow.attenuation_at_1550_nm if rrow else ""
    #     ws[f"J{row}"] = rrow.attenuation_at_1625_nm if rrow else ""

    #     for col in "FGHIJ":
    #         ws[f"{col}{row}"].border = border
    #         ws[f"{col}{row}"].alignment = align_center
    # current_row = start_row + len(part1_rows)

    # --- Left Table (A-F) ---
    for j, (tube, lrow) in enumerate(part1_rows):
        row = start_row + j
        ws[f"A{row}"] = j + 1
        if j % merge_block == 0:
            merge_end = row + min(merge_block, len(part1_rows) - j) - 1
            ws.merge_cells(start_row=row, start_column=2, end_row=merge_end, end_column=2)
            ws[f"B{row}"] = tube
            ws[f"B{row}"].alignment = align_center

        ws[f"C{row}"] = lrow.fiber_colour if lrow else ""
        ws[f"D{row}"] = lrow.attenuation_at_1310_nm if lrow else ""
        ws[f"E{row}"] = lrow.attenuation_at_1550_nm if lrow else ""
        ws[f"F{row}"] = lrow.attenuation_at_1625_nm if lrow else ""

        for col in "ABCDEF":
            ws[f"{col}{row}"].border = border
            ws[f"{col}{row}"].alignment = align_center

    # --- Right Table (G-L) ---
    for j, (tube, rrow) in enumerate(part2_rows):
        row = start_row + j
        ws[f"G{row}"] = j + 1 + len(part1_rows)
        if j % merge_block == 0:
            merge_end = row + min(merge_block, len(part2_rows) - j) - 1
            ws.merge_cells(start_row=row, start_column=8, end_row=merge_end, end_column=8)
            ws[f"H{row}"] = tube
            ws[f"H{row}"].alignment = align_center

        ws[f"I{row}"] = rrow.fiber_colour if rrow else ""
        ws[f"J{row}"] = rrow.attenuation_at_1310_nm if rrow else ""
        ws[f"K{row}"] = rrow.attenuation_at_1550_nm if rrow else ""
        ws[f"L{row}"] = rrow.attenuation_at_1625_nm if rrow else ""

        for col in "GHIJKL":
            ws[f"{col}{row}"].border = border
            ws[f"{col}{row}"].alignment = align_center

    current_row = start_row + len(part1_rows)


    

    ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row+4, end_column=7)
    cell = ws.cell(row=current_row, column=1)
    cell.value = f"Remark :\n{doc.remarks or ''}"
    cell.font = normal_font  
    cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)

    ws.merge_cells(start_row=current_row+5, start_column=4, end_row=current_row+5, end_column=7)
    ws.merge_cells(start_row=current_row+5, start_column=1, end_row=current_row+5, end_column=3)
    cell1= ws.cell(row=current_row+5, column=1, value="Prod. Operator Name: ")
    ws.cell(row=current_row+5, column=4, value = ( doc.custom_operator or ''))
    ws.merge_cells(start_row=current_row, start_column=8, end_row=current_row, end_column=12)
    bold_font = Font(bold=True)

    cell = ws.cell(row=current_row, column=8, value="Visual Inspection")
    cell.font = bold_font
    cell1.font = bold_font
    
    ws.merge_cells(start_row=current_row+1, start_column=8, end_row=current_row+4, end_column=12)
    ws.cell(
        row=current_row+1,
        column=8,
        value=f"No. Of Filler: \n"
            f"Tube sequence:\n"
            f"WBT Width(mm): \n"
            f"Lay Length(mm):"
    )

 
    ws.merge_cells(start_row=current_row+5, start_column=9, end_row=current_row+5, end_column=12)
    ws.merge_cells(start_row=current_row+5, start_column=8, end_row=current_row+5, end_column=8)
    ws.cell(row=current_row+5, column=8, value="Shift Engg. Name: ")
    ws.cell(row=current_row+5, column=9, value= (doc.custom_production_shift_engineering_name or ''))
    
    ws.merge_cells(start_row=current_row+6, start_column=3, end_row=current_row+6, end_column=7)
    ws.merge_cells(start_row=current_row+6, start_column=1, end_row=current_row+6, end_column=2)
    ws.cell(row=current_row+6, column=1, value="Tested by: ")
    ws.cell(row=current_row+6, column=3, value=(doc.inspected_by or ''))
    
    ws.cell(row=current_row+6, column=8, value="Sign & Date: " + (frappe.utils.formatdate(frappe.utils.today(), 'dd-MM-YYYY')))
    for row in ws.iter_rows(min_row=7, max_row=8, min_col=9,max_col=9):
        for cell in row:
            cell.border = border
            cell.alignment = align_left
    ws.merge_cells(start_row=current_row+6, start_column=3, end_row=current_row+6, end_column=7)
    ws.merge_cells(start_row=current_row+6, start_column=8, end_row=current_row+6, end_column=12)
    for row in ws.iter_rows(min_row=ws.max_row-8, max_row=ws.max_row, min_col=1, max_col=12):
        for cell in row:
            cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
            cell.border = border
    for row in ws.iter_rows(min_row=7, max_row=ws.max_row-7, max_col=12):
        for cell in row:
            cell.border = border
            cell.alignment = align_center
    column_widths = {
    "H": 15,"E":15,"B":15,"C":15,
    "I": 15,
    "J": 15,
    }
    for row in ws.iter_rows(min_row=4, max_row=6, max_col=12):
        for cell in row:
            cell.border = border
            cell.alignment = align_left
    for row in ws.iter_rows(min_row=7, max_row=7,min_col=6, max_col=6):
        for cell in row:
            cell.border = border
            cell.alignment = align_left
    for row in ws.iter_rows(min_row=7, max_row=7,min_col=9, max_col=9):
        for cell in row:
            cell.border = border
            cell.alignment = align_left
    for row in ws.iter_rows(min_row=8, max_row=8,min_col=8, max_col=8):
        for cell in row:
            cell.border = border
            cell.alignment = align_left
    for col, width in column_widths.items():
        ws.column_dimensions[col].width = width
    xlsx_file = BytesIO()
    wb.save(xlsx_file)
    xlsx_file.seek(0)
    return xlsx_file


# import frappe
# from openpyxl import Workbook
# from openpyxl.styles import Font, Alignment, Border, Side
# from openpyxl.drawing.image import Image
# from six import BytesIO
# from datetime import datetime
# import os

# @frappe.whitelist()
# def download_test_report(docname):
#     filename = "Stranding Single Mode"
#     xlsx_file = make_test_report(docname)
#     frappe.response['filename'] = filename + '.xlsx'
#     frappe.response['filecontent'] = xlsx_file.getvalue()
#     frappe.response['type'] = 'binary'


# def make_test_report(docname):
#     doc = frappe.get_doc("Quality Inspection", docname)

#     wb = Workbook()
#     ws = wb.active
#     ws.title = "OTDR Test Report"
#     border = Border(
#         left=Side(border_style='thin'),
#         right=Side(border_style='thin'),
#         top=Side(border_style='thin'),
#         bottom=Side(border_style='thin')
#     )
#     align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
#     align_left = Alignment(horizontal="left", vertical="center")

#     for row in ws["D1:J2"]:
#         for cell in row:
#             cell.border = border

#     for row in ws["D3:J3"]:
#         for cell in row:
#             cell.border = border

#     ws.merge_cells("A1:C3")
#     ws.merge_cells("D1:J2")
#     ws.merge_cells("D3:J3")
#     ws["D3"].border = border
#     ws["D1"] = "TAIHAN KUWAIT FIBER OPTIC CABLE CO"
#     ws["D1"].font = Font(size=14, bold=True)
#     ws["D1"].alignment = align_center
#     ws["D3"] = "OTDR Test Report - Stranding Line"
#     ws["D3"].font = Font(size=11, bold=True)
#     file_url = "/files/Taihan Kuwait logo1_page-0001 (1).jpg"
#     file_path = frappe.get_site_path("public", file_url.lstrip("/"))
#     ws["D3"].alignment = align_center

#     try:
#         if os.path.exists(file_path):
#             img = Image(file_path)
#             img.width, img.height = 100, 50
#             ws.add_image(img, "B1")
#         else:
#             fallback_logo = frappe.get_site_path("public", "files", "logo.png")
#             if os.path.exists(fallback_logo):
#                 img = Image(fallback_logo)
#                 img.width, img.height = 120, 60
#                 ws.add_image(img, "A1")
#             else:
#                 ws["B1"] = "LOGO"
#     except Exception as e:
#         ws["B1"] = "LOGO"

#     customer = frappe.db.get_value("Sales Order", {"name": doc.sales_order}, "customer")
#     ws.merge_cells("A4:B4"); ws["A4"] = "Customer:"
#     ws.merge_cells("C4:G4"); ws["C4"] = customer or ''
#     ws.merge_cells("H4:H4"); ws["H4"] = "Fiber Count"
#     ws.merge_cells("I4:J4"); ws["I4"] = doc.custom_fiber_count or ''
#     manu_date = frappe.db.get_value("Job Card", {"name": doc.reference_name}, "posting_date")

#     ws.merge_cells("A5:B5"); ws["A5"] = "Sales Order No:"
#     ws.merge_cells("C5:D5"); ws["C5"] = doc.sales_order or ''
#     ws["E5"] = "Mfg Date :"
#     ws.merge_cells("F5:G5"); ws["F5"] = frappe.utils.formatdate(manu_date) if manu_date else ""
#     ws["H5"] = "SZ Core ID:"
#     ws.merge_cells("I5:J5"); ws["I5"] = doc.custom_sz_core_id or ''

#     ws["F7"].alignment = align_left
#     ws["H8"].alignment = align_left
#     ws.merge_cells("A6:B6")
#     ws["A6"] = "OTDR No:" + (doc.custom_otdr_no or '')

#     ws["C6"] = "Fiber Type:"
#     ws["D6"] = doc.custom_fiber_type or ''
#     ws["E6"] = "Shift :"
#     ws.merge_cells("F6:G6"); ws["F6"] = doc.custom_shift or ''
#     ws["H6"] = "Drum No:"
#     ws.merge_cells("I6:J6"); ws["I6"] = doc.custom_drum_no or ''

#     ws.merge_cells("A7:A8"); ws["A7"] = "IOR"
#     ws["B7"] = "1310nm"
#     ws["C7"] = "1550nm"
#     ws["D7"] = "1625nm"
#     ws["E7"] = "Core OD(mm):"
#     ws.merge_cells("F7:G7"); ws["F7"] = doc.custom_core_odmm or ''
#     ws["H7"] = "Prod.Length (M):"
#     ws.merge_cells("I7:J7"); ws["I7"] = doc.custom_production_length or ''

#     ws["B8"] = doc.custom_ior__1310_nm or ""
#     ws["C8"] = doc.custom_ior__1550_nm or ""
#     ws["D8"] = doc.custom_ior__1625_nm or ""
#     ws["E8"] = "FRP OD (mm):"
#     ws.merge_cells("F8:G8"); ws["F8"] = doc.custom_frp_od or ''
#     bold_font = Font(bold=True)
#     normal_font = Font(bold=False)
#     ws.merge_cells("H8:J8")
#     ws["H8"] = f"OTDR Length (M): {doc.custom_otdr_lengthm:.2f}" if doc.custom_otdr_lengthm else "OTDR Length (M):"
#     ws["H8"].alignment = align_left

#     # --- Headers for Left and Right Tables ---
#     ws.merge_cells("A9:A11"); ws["A9"] = "S.No"; ws["A9"].font = bold_font
#     ws.merge_cells("B9:B11"); ws["B9"] = "Tube Colour"; ws["B9"].font = bold_font
#     ws.merge_cells("C9:C11"); ws["C9"] = "Fiber Colour"; ws["C9"].font = bold_font
#     ws.merge_cells("D9:F9"); ws["D9"] = "Attenuation dB/km"; ws["D9"].font = bold_font

#     ws.merge_cells("G9:G11"); ws["G9"] = "S.No"; ws["G9"].font = bold_font
#     ws.merge_cells("H9:H11"); ws["H9"] = "Tube Colour"; ws["H9"].font = bold_font
#     ws.merge_cells("I9:I11"); ws["I9"] = "Fiber Colour"; ws["I9"].font = bold_font
#     ws.merge_cells("J9:L9"); ws["J9"] = "Attenuation dB/km"; ws["J9"].font = bold_font

#     ws["D10"] = "1310 nm"; ws["E10"] = "1550 nm"; ws["F10"] = "1625 nm"
#     ws["J10"] = "1310 nm"; ws["K10"] = "1550 nm"; ws["L10"] = "1625 nm"

#     from collections import defaultdict

#     grouped_rows = defaultdict(list)
#     for row in doc.custom_stranding_attenuation:
#         grouped_rows[row.tube_colour].append(row)

#     all_rows = []
#     for tube in grouped_rows:
#         for row in grouped_rows[tube]:
#             all_rows.append((tube, row))

#     total_fibers = len(all_rows)

#     if total_fibers <= 12:
#         part1_rows = all_rows
#         part2_rows = []
#     else:
#         half = total_fibers // 2
#         part1_rows = all_rows[:half]
#         part2_rows = all_rows[half:]

#     start_row = 12
#     merge_block = 12

#     # --- Left Table (A-F) ---
#     for j, (tube, lrow) in enumerate(part1_rows):
#         row = start_row + j
#         ws[f"A{row}"] = j + 1
#         if j % merge_block == 0:
#             merge_end = row + min(merge_block, len(part1_rows) - j) - 1
#             ws.merge_cells(start_row=row, start_column=2, end_row=merge_end, end_column=2)
#             ws[f"B{row}"] = tube
#             ws[f"B{row}"].alignment = align_center

#         ws[f"C{row}"] = lrow.fiber_colour if lrow else ""
#         ws[f"D{row}"] = lrow.attenuation_at_1310_nm if lrow else ""
#         ws[f"E{row}"] = lrow.attenuation_at_1550_nm if lrow else ""
#         ws[f"F{row}"] = lrow.attenuation_at_1625_nm if lrow else ""

#         for col in "ABCDEF":
#             ws[f"{col}{row}"].border = border
#             ws[f"{col}{row}"].alignment = align_center

#     # --- Right Table (G-L) ---
#     for j, (tube, rrow) in enumerate(part2_rows):
#         row = start_row + j
#         ws[f"G{row}"] = j + 1
#         if j % merge_block == 0:
#             merge_end = row + min(merge_block, len(part2_rows) - j) - 1
#             ws.merge_cells(start_row=row, start_column=8, end_row=merge_end, end_column=8)
#             ws[f"H{row}"] = tube
#             ws[f"H{row}"].alignment = align_center

#         ws[f"I{row}"] = rrow.fiber_colour if rrow else ""
#         ws[f"J{row}"] = rrow.attenuation_at_1310_nm if rrow else ""
#         ws[f"K{row}"] = rrow.attenuation_at_1550_nm if rrow else ""
#         ws[f"L{row}"] = rrow.attenuation_at_1625_nm if rrow else ""

#         for col in "GHIJKL":
#             ws[f"{col}{row}"].border = border
#             ws[f"{col}{row}"].alignment = align_center

#     current_row = start_row + len(part1_rows)

#     # --- Remarks and footer ---
#     ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row+4, end_column=7)
#     cell = ws.cell(row=current_row, column=1)
#     cell.value = f"Remark :\n{doc.remarks or ''}"
#     cell.font = normal_font
#     cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)

#     ws.merge_cells(start_row=current_row+5, start_column=4, end_row=current_row+5, end_column=7)
#     ws.merge_cells(start_row=current_row+5, start_column=1, end_row=current_row+5, end_column=3)
#     cell1 = ws.cell(row=current_row+5, column=1, value="Prod. Operator Name: ")
#     ws.cell(row=current_row+5, column=4, value=(doc.custom_operator or ''))

#     ws.merge_cells(start_row=current_row, start_column=8, end_row=current_row, end_column=10)
#     cell = ws.cell(row=current_row, column=8, value="Visual Inspection")
#     cell.font = bold_font
#     cell1.font = bold_font

#     ws.merge_cells(start_row=current_row+1, start_column=8, end_row=current_row+4, end_column=10)
#     ws.cell(
#         row=current_row+1,
#         column=8,
#         value=f"No. Of Filler: \nTube sequence:\nWBT Width(mm): \nLay Length(mm):"
#     )

#     ws.merge_cells(start_row=current_row+5, start_column=9, end_row=current_row+5, end_column=10)
#     ws.merge_cells(start_row=current_row+5, start_column=8, end_row=current_row+5, end_column=8)
#     ws.cell(row=current_row+5, column=8, value="Shift Engg. Name: ")
#     ws.cell(row=current_row+5, column=9, value=(doc.custom_production_shift_engineering_name or ''))

#     ws.merge_cells(start_row=current_row+6, start_column=3, end_row=current_row+6, end_column=7)
#     ws.merge_cells(start_row=current_row+6, start_column=1, end_row=current_row+6, end_column=2)
#     ws.cell(row=current_row+6, column=1, value="Tested by: ")
#     ws.cell(row=current_row+6, column=3, value=(doc.inspected_by or ''))
#     ws.cell(row=current_row+6, column=8, value="Sign & Date: " + frappe.utils.formatdate(frappe.utils.today(), 'dd-MM-YYYY'))

#     for col, width in {
#         "A": 8, "B": 15, "C": 15, "D": 15, "E": 15, "F": 15,
#         "G": 8, "H": 15, "I": 15, "J": 15, "K": 15, "L": 15
#     }.items():
#         ws.column_dimensions[col].width = width

#     for row in ws.iter_rows(min_row=4, max_row=6, max_col=10):
#         for cell in row:
#             cell.border = border
#             cell.alignment = align_left
#     for row in ws.iter_rows(min_row=7, max_row=7,min_col=6, max_col=6):
#         for cell in row:
#             cell.border = border
#             cell.alignment = align_left
#     for row in ws.iter_rows(min_row=7, max_row=7,min_col=9, max_col=9):
#         for cell in row:
#             cell.border = border
#             cell.alignment = align_left
#     for row in ws.iter_rows(min_row=8, max_row=8,min_col=8, max_col=8):
#         for cell in row:
#             cell.border = border
#             cell.alignment = align_left

#     xlsx_file = BytesIO()
#     wb.save(xlsx_file)
#     xlsx_file.seek(0)
#     return xlsx_file
