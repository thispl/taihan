import frappe
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.drawing.image import Image
from six import BytesIO
from datetime import datetime
import os

@frappe.whitelist()
def download_jacketing_qc_single(docname):
    filename = "Jacketing Single Mode"
    xlsx_file = make_jacketing_qc_single(docname)
    frappe.response['filename'] = filename + '.xlsx'
    frappe.response['filecontent'] = xlsx_file.getvalue()
    frappe.response['type'] = 'binary'
    


def make_jacketing_qc_single(docname):
    doc = frappe.get_doc("Quality Inspection",docname)
    wb = Workbook()
    ws = wb.active
    ws.title = "OTDR Test Report - Single Mode"
    
    
    border = Border(
        left=Side(border_style='thin'),
        right=Side(border_style='thin'),
        top=Side(border_style='thin'),
        bottom=Side(border_style='thin')
    )
    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    align_left = Alignment(horizontal="left", vertical="top", wrap_text=True)
    bold_font = Font(bold=True)
    normal_font = Font(bold=False)
    
    for row in ws["A1:L12"]:
        for cell in row:
            cell.border = border
    
    ws.merge_cells("A1:C3")
    ws.merge_cells("D1:L2")
    ws.merge_cells("D3:L3")
    
    ws["D1"] = "TAIHAN KUWAIT FIBER OPTIC CABLE CO"
    ws["D1"].font = Font(size=14, bold=True)
    ws["D1"].alignment = align_center
    
    ws["D3"]="OTDR Test Report - Single Mode"
    ws["D3"].font = Font(size=12)
    ws["D3"].alignment = align_center
    
    
    file_url = "/files/Taihan Kuwait logo1_page-0001 (1).jpg"
    file_path = frappe.get_site_path("public", file_url.lstrip("/"))
    try:
        if os.path.exists(file_path):
            img = Image(file_path)
            img.width, img.height = 100, 50
            ws.add_image(img, "A1")
        else:
            ws["A1"] = "LOGO"
    except:
        ws["A1"] = "LOGO"
    ws["A1"].alignment=align_center
    
    
    customer = frappe.db.get_value("Sales Order", {"name": doc.sales_order}, "customer")
    manu_date = frappe.db.get_value("Job Card",{"name":doc.reference_name},"posting_date")
    
    ws.merge_cells("A4:B4") 
    ws.merge_cells("c4:D4")
    ws.merge_cells("E4:I4")
    ws.merge_cells("J4:K4")
    
    ws["A4"] = "Customer:"
    ws["A4"].font =  bold_font
    ws["A4"].alignment = align_center
    ws["c4"] = customer
    ws["J4"] = "Fiber Count:"
    ws["J4"].font = bold_font
    ws["J4"].alignment = align_center
    ws["L4"] = doc.custom_fiber_count or ""
    
    
    ws.merge_cells("A5:B5")
    ws.merge_cells("C5:D5")
    ws.merge_cells("F5:I5")
    ws.merge_cells("J5:K5")
    
    ws["A5"]="Sales Order No:"
    ws["A5"].alignment = align_center
    ws["A5"].font = bold_font
    ws["c5"]=doc.sales_order or ""
    ws["E5"]="Date:"
    ws["E5"].alignment = align_center
    ws["E5"].font = bold_font
    ws["F5"]=frappe.utils.formatdate(doc.report_date) if doc.report_date else ""
    ws["J5"]="Sheathing ID:"
    ws["J5"].alignment = align_center
    ws["J5"].font = bold_font
    ws["L5"]=doc.custom_sheathing_id or ""
    
    
    ws.merge_cells("A6:B6")
    ws.merge_cells("C6:D6")
    ws.merge_cells("E6:G6")
    ws.merge_cells("J6:K6")
    
    ws["A6"]="Cable Type:"
    ws["A6"].alignment = align_center
    ws["A6"].font = bold_font
    ws["C6"]=doc.custom_cable_type or ""
    ws["E6"]="Cable Dimension (mm)"
    ws["E6"].alignment = align_center
    ws["E6"].font = bold_font
    ws["H6"]="Min"
    ws["I6"]="Max"
    ws["J6"]="Drum No:"
    ws["J6"].alignment = align_center
    ws["J6"].font = bold_font
    ws["L6"]=doc.custom_drum_no or ""
    
    
    ws.merge_cells("A7:B7")
    ws.merge_cells("C7:D7")
    ws.merge_cells("E7:G7")
    ws.merge_cells("J7:K7")
    
    ws["A7"]="Fiber Type:"
    ws["A7"].font = bold_font
    ws["A7"].alignment = align_center
    ws["C7"]=doc.custom_fiber_type or ""
    ws["E7"]="Inner sh OD"
    ws["E7"].font = bold_font
    ws["E7"].alignment = align_center
    ws["H7"]=doc.custom_inner_sh__od or ""
    ws["I7"]=doc.custom_inner_sh__od_max or ""
    ws["J7"]="Bottom Marking (M):"
    ws["J7"].alignment = align_center
    ws["J7"].font = bold_font
    ws["L7"]=doc.custom_bottom_marking or ""
    
    
    
    ws.merge_cells("E8:G8")
    ws.merge_cells("J8:K8")
    
    ws["A8"]="OTDR No:"
    ws["A8"].alignment = align_center
    ws["A8"].font = bold_font
    ws["B8"]=doc.custom_otdr_no or ""
    ws["C8"]="Shift:"
    ws["C8"].alignment = align_center
    ws["C8"].font = bold_font
    ws["D8"]=doc.custom_shift or ""
    ws["E8"]="Inner sh Thickness"
    ws["E8"].alignment = align_center
    ws["E8"].font = bold_font
    ws["H8"]=doc.custom_inner_sh_thickness_min or ""
    ws["I8"]=doc.custom_inner_sh_thickness_max or ""
    ws["J8"]="Top Marking (M):"
    ws["J8"].alignment = align_center
    ws["J8"].font = bold_font
    ws["L8"]=doc.custom_top_marking or ""
    
    ws.merge_cells("A9:A10")
    ws.merge_cells("E9:G9")
    ws.merge_cells("J9:K9")
    
    
    ws["A9"]="IOR"
    ws["A9"].alignment = align_center
    ws["A9"].font = bold_font
    ws["B9"]="1310nm"
    ws["C9"]="1550nm"
    ws["D9"]="1625nm"
    ws["E9"]="Cable Outer OD"
    ws["E9"].alignment = align_center
    ws["E9"].font = bold_font
    ws["H9"]=doc.custom_cable_outer_od or ""
    ws["I9"]=doc.custom_cable_outer_od_max or ""
    ws["J9"]="Prod. Length (M):"
    ws["J9"].alignment = align_center
    ws["J9"].font = bold_font
    ws["L9"]=doc.custom_production_length or ""
    
    
    ws["B10"]=doc.custom_ior__1310_nm or ""
    ws["C10"]=doc.custom_ior__1550_nm or ""
    ws["D10"]=doc.custom_ior__1625_nm or ""
    
    ws.merge_cells("E10:G10")
    ws.merge_cells("J10:K10")
    
    ws["E10"]="Cable Thickness"
    ws["E10"].alignment = align_center
    ws["E10"].font = bold_font
    ws["H10"]=doc.custom_cable_thickness_min or ""
    ws["I10"]=doc.custom_cable_thickness_max or ""
    ws["J10"]="OTDR Length (M):"
    ws["J10"].alignment = align_center
    ws["J10"].font = bold_font
    ws["L10"]=doc.custom_otdr_lengthm or ""
    
    
    # ws.merge_cells("A11:A12")
    # ws.merge_cells("B11:B12")
    # ws.merge_cells("C11:C12")
    # ws.merge_cells("D11:F11")
    # ws.merge_cells("G11:G12")
    # ws.merge_cells("H11:H12")
    # ws.merge_cells("I11:I12")
    # ws.merge_cells("J11:L11")
    
    # ws["A11"]="Tube Colour"
    # ws["A11"].alignment = align_center
    # ws["A11"].font = bold_font
    # ws["B11"]="SL. No"
    # ws["B11"].alignment = align_center
    # ws["B11"].font = bold_font
    # ws["C11"]="Fiber Colour"
    # ws["C11"].alignment = align_center
    # ws["C11"].font = bold_font
    # ws["D11"]="Attenuation dB/km"
    # ws["D11"].alignment = align_center
    # ws["D11"].font = bold_font
    # ws["D12"]="1310nm"
    # ws["D12"].alignment = align_center
    # ws["D12"].font = bold_font
    # ws["E12"]="1550nm"
    # ws["E12"].alignment = align_center
    # ws["E12"].font = bold_font
    # ws["F12"]="1625nm"
    # ws["F12"].alignment = align_center
    # ws["F12"].font = bold_font
    # ws["G11"]="Colour"
    # ws["G11"].alignment = align_center
    # ws["G11"].font = bold_font
    # ws["H11"]="SL. No"
    # ws["H11"].alignment = align_center
    # ws["H11"].font = bold_font
    # ws["I11"]="Fiber Colour"
    # ws["I11"].alignment = align_center
    # ws["I11"].font = bold_font
    # ws["J11"]="Attenuation dB/km"
    # ws["J11"].alignment = align_center
    # ws["J11"].font = bold_font
    # ws["J12"]="1310nm"
    # ws["J12"].alignment = align_center
    # ws["J12"].font = bold_font
    # ws["K12"]="1550nm"
    # ws["K12"].alignment = align_center
    # ws["K12"].font = bold_font
    # ws["L12"]="1625nm"
    # ws["L12"].alignment = align_center
    # ws["L12"].font = bold_font

        # ===== Table Headers =====
    ws.merge_cells("A11:A12")
    ws.merge_cells("B11:B12")
    ws.merge_cells("C11:C12")
    ws.merge_cells("D11:F11")
    ws.merge_cells("G11:G12")
    ws.merge_cells("H11:H12")
    ws.merge_cells("I11:I12")
    ws.merge_cells("J11:L11")

    # ---- LEFT SIDE ----
    ws["A11"] = "S.No"
    ws["A11"].alignment = align_center
    ws["A11"].font = bold_font

    ws["B11"] = "Tube Colour"
    ws["B11"].alignment = align_center
    ws["B11"].font = bold_font

    ws["C11"] = "Fiber Colour"
    ws["C11"].alignment = align_center
    ws["C11"].font = bold_font

    ws["D11"] = "Attenuation dB/km"
    ws["D11"].alignment = align_center
    ws["D11"].font = bold_font
    ws["D12"] = "1310nm"
    ws["E12"] = "1550nm"
    ws["F12"] = "1625nm"
    for col in ["D12", "E12", "F12"]:
        ws[col].alignment = align_center
        ws[col].font = bold_font

    # ---- RIGHT SIDE ----
    ws["G11"] = "S.No"
    ws["G11"].alignment = align_center
    ws["G11"].font = bold_font

    ws["H11"] = "Tube Colour"
    ws["H11"].alignment = align_center
    ws["H11"].font = bold_font

    ws["I11"] = "Fiber Colour"
    ws["I11"].alignment = align_center
    ws["I11"].font = bold_font

    ws["J11"] = "Attenuation dB/km"
    ws["J11"].alignment = align_center
    ws["J11"].font = bold_font
    ws["J12"] = "1310nm"
    ws["K12"] = "1550nm"
    ws["L12"] = "1625nm"
    for col in ["J12", "K12", "L12"]:
        ws[col].alignment = align_center
        ws[col].font = bold_font

    from collections import defaultdict

    grouped_rows = defaultdict(list)
    for row in doc.custom_jacketing_attenuation:
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


    start_row = 13
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
    # --- Left Table (A-F) ---
    for j, (tube, lrow) in enumerate(part1_rows):
        row = start_row + j

        # Serial number in column A (do not write if merged)
        ws[f"A{row}"] = j + 1  # Ensure column A is NOT merged elsewhere

        # Merge Tube Colour in column B
        if j % merge_block == 0:
            merge_end = row + min(merge_block, len(part1_rows) - j) - 1
            if merge_end > row:  # only merge if more than 1 row
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



    
    
   
    
    

    # serial_left, serial_right = 1, 1
    # current_row = 13


    # for i in range(0, len(tube_colours), 2):
    #     left_tube = tube_colours[i]
    #     right_tube = tube_colours[i + 1] if i + 1 < len(tube_colours) else None

    #     left_rows = grouped_rows[left_tube]
    #     right_rows = grouped_rows[right_tube] if right_tube else []

    #     max_rows = max(len(left_rows), len(right_rows))

    #     for j in range(max_rows):
    #         row = current_row

           
    #         lrow = left_rows[j] if j < len(left_rows) else None
    #         if j == 0 and left_rows:  
    #             ws.merge_cells(start_row=row, start_column=1, end_row=row+len(left_rows)-1, end_column=1)
    #             ws[f"A{row}"] = left_tube
    #             ws[f"A{row}"].alignment = align_center

    #         if lrow:
    #             ws[f"B{row}"] = serial_left
    #             ws[f"C{row}"] = lrow.fiber_colour
    #             ws[f"D{row}"] = lrow.attenuation_at_1310_nm
    #             ws[f"E{row}"] = lrow.attenuation_at_1550_nm
    #             ws[f"F{row}"] = lrow.attenuation_at_1625_nm
    #             serial_left += 1

           
    #         rrow = right_rows[j] if j < len(right_rows) else None
    #         if right_tube and j == 0 and right_rows:  
    #             ws.merge_cells(start_row=row, start_column=7, end_row=row+len(right_rows)-1, end_column=7)
    #             ws[f"G{row}"] = right_tube
    #             ws[f"G{row}"].alignment = align_center

    #         if rrow:
    #             ws[f"H{row}"] = serial_right
    #             ws[f"I{row}"] = rrow.fiber_colour
    #             ws[f"J{row}"] = rrow.attenuation_at_1310_nm
    #             ws[f"K{row}"] = rrow.attenuation_at_1550_nm
    #             ws[f"L{row}"] = rrow.attenuation_at_1625_nm
    #             serial_right += 1

            
    #         for col in "ABCDEFGHIJKL":
    #             ws[f"{col}{row}"].border = border
    #             ws[f"{col}{row}"].alignment = align_center

    #         current_row += 1

    # serial_left, serial_right = 1, 1
    # current_row = 13

    # for i in range(0, len(tube_colours), 2):
    #     left_tube = tube_colours[i]
    #     right_tube = tube_colours[i + 1] if i + 1 < len(tube_colours) else None

    #     left_rows = grouped_rows[left_tube]
    #     right_rows = grouped_rows[right_tube] if right_tube else []

    #     max_rows = max(len(left_rows), len(right_rows))

    #     for j in range(max_rows):
    #         row = current_row

    #         # ---- LEFT SIDE ----
    #         lrow = left_rows[j] if j < len(left_rows) else None
    #         if j == 0 and left_rows:
    #             ws.merge_cells(start_row=row, start_column=2, end_row=row+len(left_rows)-1, end_column=2)
    #             ws[f"B{row}"] = left_tube
    #             ws[f"B{row}"].alignment = align_center

    #         if lrow:
    #             ws[f"A{row}"] = serial_left
    #             ws[f"C{row}"] = lrow.fiber_colour
    #             ws[f"D{row}"] = lrow.attenuation_at_1310_nm
    #             ws[f"E{row}"] = lrow.attenuation_at_1550_nm
    #             ws[f"F{row}"] = lrow.attenuation_at_1625_nm
    #             serial_left += 1

    #         # ---- RIGHT SIDE ----
    #         rrow = right_rows[j] if j < len(right_rows) else None
    #         if right_tube and j == 0 and right_rows:
    #             ws.merge_cells(start_row=row, start_column=8, end_row=row+len(right_rows)-1, end_column=8)
    #             ws[f"H{row}"] = right_tube
    #             ws[f"H{row}"].alignment = align_center

    #         if rrow:
    #             ws[f"G{row}"] = serial_right
    #             ws[f"I{row}"] = rrow.fiber_colour
    #             ws[f"J{row}"] = rrow.attenuation_at_1310_nm
    #             ws[f"K{row}"] = rrow.attenuation_at_1550_nm
    #             ws[f"L{row}"] = rrow.attenuation_at_1625_nm
    #             serial_right += 1

    #         for col in "ABCDEFGHIJKL":
    #             ws[f"{col}{row}"].border = border
    #             ws[f"{col}{row}"].alignment = align_center

    #         current_row += 1


    
    thin_border = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
    
)
    bold_font = Font(bold=True)
    
    for row in ws[f"A{current_row+1}:L{current_row+6}"]:
        for cell in row:
            cell.border = border
    
    ws.merge_cells(start_row=current_row+1, start_column=1, end_row=current_row+4, end_column=12)
    cell = ws.cell(row=current_row+1, column=1)
    cell.value = f"Remark :\n{doc.remarks or ''}"
    cell.font = bold_font
    cell.border = thin_border  
    cell.alignment = Alignment(horizontal="center", vertical="top" , wrap_text=True)

    ws.merge_cells(start_row=current_row+5, start_column=1, end_row=current_row+5, end_column=4)
    ws.merge_cells(start_row=current_row+5, start_column=5, end_row=current_row+5, end_column=6)
    cell1= ws.cell(row=current_row+5, column=1, value="Production Operator: ")
    ws.cell(row=current_row+5, column=5, value = ( doc.custom_operator or '')).border = thin_border
    cell1.font = bold_font
    cell1.border = thin_border
    
    ws.merge_cells(start_row=current_row+5, start_column=7, end_row=current_row+5, end_column=10)
    ws.merge_cells(start_row=current_row+5, start_column=11, end_row=current_row+5, end_column=12)
    cell2=ws.cell(row=current_row+5, column=7, value="Prod. Shift Engg. Name: ")
    ws.cell(row=current_row+5, column=11, value = ( doc.custom_production_shift_engineering_name or '')).border = thin_border
    cell2.font = bold_font
    cell2.border = thin_border
    
    ws.merge_cells(start_row=current_row+6, start_column=1, end_row=current_row+6, end_column=2)
    ws.merge_cells(start_row=current_row+6, start_column=3, end_row=current_row+6, end_column=6)
    cell3=ws.cell(row=current_row+6, column=1, value="Tested by ")
    ws.cell(row=current_row+6, column=3, value = ( doc.inspected_by or '')).border = thin_border
    cell3.font = bold_font
    cell3.border = thin_border
    
    ws.merge_cells(start_row=current_row+6, start_column=7, end_row=current_row+6, end_column=12)
    
    cell4=ws.cell(row=current_row+6, column=7, value="Sign & Date: " + ( frappe.utils.formatdate(frappe.utils.today(), 'dd-MM-YYYY')) )
    cell4.font = bold_font
    cell4.border = thin_border
    cell4.alignment = Alignment(horizontal="center")
    
    


    
        
        
        
    xlsx_file = BytesIO()
    wb.save(xlsx_file)
    xlsx_file.seek(0)
    return xlsx_file

