import frappe
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.drawing.image import Image
from six import BytesIO
from datetime import datetime
import os

@frappe.whitelist()
def download_jacketing_qc_multi(docname):
    filename = "Jacketing Multi Mode"
    xlsx_file = make_jacketing_qc_multi(docname)
    frappe.response['filename'] = filename + '.xlsx'
    frappe.response['filecontent'] = xlsx_file.getvalue()
    frappe.response['type'] = 'binary'
    


def make_jacketing_qc_multi(docname):
    doc = frappe.get_doc("Quality Inspection",docname)
    wb = Workbook()
    ws = wb.active
    ws.title = "OTDR Test Report - Multi Mode"
    
    
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
    ws["A4"].font = bold_font
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
    ws["A5"].font = bold_font
    ws["A5"].alignment = align_center
    ws["c5"]=doc.sales_order or ""
    ws["E5"]="Date:"
    ws["E5"].font = bold_font
    ws["E5"].alignment = align_center
    ws["F5"]=frappe.utils.formatdate(doc.report_date) if doc.report_date else ""
    ws["J5"]="Sheathing ID:"
    ws["J5"].font = bold_font
    ws["J5"].alignment = align_center
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
    ws["E6"].font = bold_font
    ws["E6"].alignment = align_center
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
    ws["E7"].alignment = align_center
    ws["E7"].font = bold_font
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
    ws["C8"].font = bold_font
    ws["C8"].alignment = align_center
    ws["D8"]=doc.custom_shift or ""
    ws["E8"]="Inner sh Thickness"
    ws["E8"].alignment = align_center
    ws["E8"].font = bold_font
    ws["H8"]=doc.custom_inner_sh_thickness_min or ""
    ws["I8"]=doc.custom_inner_sh_thickness_max or ""
    ws["J8"]="Top Marking (M):"
    ws["J8"].font = bold_font
    ws["J8"].alignment = align_center
    ws["L8"]=doc.custom_top_marking or ""
    
    ws.merge_cells("A9:B10")
    ws.merge_cells("E9:G9")
    ws.merge_cells("J9:K9")
    
    
    ws["A9"]="IOR"
    ws["A9"].alignment = align_center
    ws["A9"].font = bold_font
    
    ws["C9"]="850nm"
    ws["D9"]="1300nm"
    ws["E9"]="Cable Outer OD"
    ws["E9"].alignment = align_center
    ws["E9"].font = bold_font
    ws["H9"]=doc.custom_cable_outer_od or ""
    ws["I9"]=doc.custom_cable_outer_od_max or ""
    ws["J9"]="Prod. Length (M):"
    ws["J9"].font = bold_font
    ws["J9"].alignment = align_center
    ws["L9"]=doc.custom_production_length or ""
    
    
    
    ws["C10"]=doc.custom_ior__850_nm or ""
    ws["D10"]=doc.custom_ior__1300_nm or ""
    
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
    
    
    ws.merge_cells("A11:A12")
    ws.merge_cells("B11:B12")
    ws.merge_cells("C11:D12")
    ws.merge_cells("E11:E12")
    ws.merge_cells("F11:F12")
    ws.merge_cells("G11:G12")
    ws.merge_cells("H11:H12")
    ws.merge_cells("I11:J12")
    ws.merge_cells("K11:K12")
    ws.merge_cells("L11:L12")
    
    # ws["A11"]="Tube Colour"
    # ws["A11"].alignment = align_center
    # ws["A11"].font = bold_font
    ws.merge_cells("A11:A12")
    ws["A11"] = "S.No"
    ws["A11"].alignment = align_center
    ws["A11"].font = bold_font
    ws["B11"]="Tube Colour"
    ws["B11"].alignment = align_center
    ws["B11"].font = bold_font

    ws["C11"]="Fiber Colour"
    ws["C11"].alignment = align_center
    ws["C11"].font = bold_font
    ws["E11"]="850nm"
    ws["E11"].alignment = align_center
    ws["E11"].font = bold_font
    ws["F11"]="1300nm"
    ws["F11"].alignment = align_center
    ws["F11"].font = bold_font
    ws.merge_cells("G11:G12")
    ws["G11"] = "S.No"
    ws["G11"].alignment = align_center
    ws["G11"].font = bold_font
    ws["H11"]="Tube Colour"
    ws["H11"].alignment = align_center
    ws["H11"].font = bold_font

    # ws["G11"]="Tube Colour"
    # ws["G11"].alignment = align_center
    # ws["G11"].font = bold_font
    ws["I11"]="Fiber Colour"
    ws["I11"].alignment = align_center
    ws["I11"].font = bold_font
    ws["K11"]="850nm"
    ws["K11"].alignment = align_center
    ws["K11"].font = bold_font
    ws["L11"]="1300nm"
    ws["L11"].alignment = align_center
    ws["L11"].font = bold_font
    
    
    
   
    
    
    # from collections import defaultdict

    
    # grouped_rows = defaultdict(list)
    # for row in doc.custom_mm_jacketing_attenuation:
    #     grouped_rows[row.tube_colour].append(row)

    
    # tube_colours = sorted(grouped_rows.keys())

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
    #             ws.merge_cells(start_row=row, start_column=1, end_row=row+len(left_rows)-1, end_column=2)
    #             ws[f"A{row}"] = left_tube
    #             ws[f"A{row}"].alignment = align_center

    #         if lrow:
    #             ws.merge_cells(start_row=row,start_column=3,end_row=row,end_column=4)
    #             ws[f"C{row}"] = lrow.fiber_colour
                
    #             ws[f"E{row}"] = lrow.attenuation_at_850_nm
    #             ws[f"F{row}"] = lrow.attenuation_at_1300_nm
    #             serial_left += 1

           
    #         rrow = right_rows[j] if j < len(right_rows) else None
    #         if right_tube and j == 0 and right_rows:  
    #             ws.merge_cells(start_row=row, start_column=7, end_row=row+len(right_rows)-1, end_column=8)
    #             ws[f"G{row}"] = right_tube
    #             ws[f"G{row}"].alignment = align_center

    #         if rrow:
    #             ws.merge_cells(start_row=row,start_column=9,end_row=row,end_column=10)
    #             ws[f"I{row}"] = rrow.fiber_colour
                
    #             ws[f"K{row}"] = rrow.attenuation_at_850_nm
    #             ws[f"L{row}"] = rrow.attenuation_at_1300_nm
    #             serial_right += 1

            
    #         for col in "ABCDEFGHIJKL":
    #             ws[f"{col}{row}"].border = border
    #             ws[f"{col}{row}"].alignment = align_center

    #         current_row += 1

    from collections import defaultdict

    grouped_rows = defaultdict(list)
    for row in doc.custom_mm_jacketing_attenuation:
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

    start_row = 13
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

        # Merge Tube column (B)
        if j % merge_block == 0:
            merge_end = row + min(merge_block, len(part1_rows) - j) - 1
            ws.merge_cells(start_row=row, start_column=2, end_row=merge_end, end_column=2)
            ws[f"B{row}"] = tube
            ws[f"B{row}"].alignment = align_center

        # Merge Fiber Colour columns (C–D)
        ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=4)
        ws[f"C{row}"] = lrow.fiber_colour or ''
        ws[f"C{row}"].alignment = align_center

        ws[f"E{row}"] = lrow.attenuation_at_850_nm or ''
        ws[f"F{row}"] = lrow.attenuation_at_1300_nm or ''

        for col in "ABCDEF":
            ws[f"{col}{row}"].border = border
            ws[f"{col}{row}"].alignment = align_center

    # --- Right table (F–J) ---
    for j, (tube, rrow) in enumerate(part2_rows):
        row = start_row + j
        ws[f"G{row}"] = j + 1 + len(part1_rows)  # Continue numbering

        # Merge Tube column (H)
        if j % merge_block == 0:
            merge_end = row + min(merge_block, len(part2_rows) - j) - 1
            ws.merge_cells(start_row=row, start_column=8, end_row=merge_end, end_column=8)
            ws[f"H{row}"] = tube
            ws[f"H{row}"].alignment = align_center

        # Merge Fiber Colour columns (I–J)
        ws.merge_cells(start_row=row, start_column=9, end_row=row, end_column=10)
        ws[f"I{row}"] = rrow.fiber_colour or ''
        ws[f"I{row}"].alignment = align_center

        ws[f"K{row}"] = rrow.attenuation_at_850_nm or ''
        ws[f"L{row}"] = rrow.attenuation_at_1300_nm or ''

        for col in "GHIJKL":
            ws[f"{col}{row}"].border = border
            ws[f"{col}{row}"].alignment = align_center

    current_row = start_row + max(len(part1_rows), len(part2_rows))



    
    thin_border = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
    
)
    bold_font = Font(bold=True)
    
    for row in ws[f"A{current_row}:L{current_row+6}"]:
        for cell in row:
            cell.border = border
    
    ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row+4, end_column=6)
    cell = ws.cell(row=current_row, column=1)
    cell.value = f"Remark :\n{doc.remarks or ''}"
    cell.font = bold_font
    cell.border = thin_border  
    cell.alignment = Alignment(horizontal="left", vertical="top" , wrap_text=True)
    
    
    
    
    ws.merge_cells(start_row=current_row, start_column=7, end_row=current_row, end_column=12)
    cell1= ws.cell(row=current_row, column=7, value="Visual Inspection ")
    cell1.font = bold_font
    cell1.border = thin_border
    cell1.alignment = Alignment(horizontal="center", vertical="top" , wrap_text=True)
    
    ws.merge_cells(start_row=current_row+1, start_column=7, end_row=current_row+1, end_column=12)
    cell2= ws.cell(row=current_row+1, column=7, value="No. Of Filler ")
    
    ws.merge_cells(start_row=current_row+2, start_column=7, end_row=current_row+2, end_column=12)
    cell7= ws.cell(row=current_row+2, column=7, value="Tube sequence: ")
    
    ws.merge_cells(start_row=current_row+3, start_column=7, end_row=current_row+3, end_column=12)
    cell8= ws.cell(row=current_row+3, column=7, value="WBT Width(mm): ")
    
    ws.merge_cells(start_row=current_row+4, start_column=7, end_row=current_row+4, end_column=12)
    cell9= ws.cell(row=current_row+4, column=7, value="Lay Length(mm): ")
    
    
   
    

    ws.merge_cells(start_row=current_row+5, start_column=1, end_row=current_row+5, end_column=4)
    ws.merge_cells(start_row=current_row+5, start_column=5, end_row=current_row+5, end_column=6)
    cell3= ws.cell(row=current_row+5, column=1, value="Production Operator: ")
    ws.cell(row=current_row+5, column=5, value = ( doc.custom_operator or '')).border = thin_border
    cell3.font = bold_font
    cell3.border = thin_border
    
    ws.merge_cells(start_row=current_row+5, start_column=7, end_row=current_row+5, end_column=10)
    ws.merge_cells(start_row=current_row+5, start_column=11, end_row=current_row+5, end_column=12)
    cell4=ws.cell(row=current_row+5, column=7, value="Prod. Shift Engg. Name: ")
    ws.cell(row=current_row+5, column=11, value = ( doc.custom_production_shift_engineering_name or '')).border = thin_border
    cell4.font = bold_font
    cell4.border = thin_border
    
    ws.merge_cells(start_row=current_row+6, start_column=1, end_row=current_row+6, end_column=2)
    ws.merge_cells(start_row=current_row+6, start_column=3, end_row=current_row+6, end_column=6)
    cell5=ws.cell(row=current_row+6, column=1, value="Tested by ")
    ws.cell(row=current_row+6, column=3, value = ( doc.inspected_by or '')).border = thin_border
    cell5.font = bold_font
    cell5.border = thin_border
    
    ws.merge_cells(start_row=current_row+6, start_column=7, end_row=current_row+6, end_column=12)
    
    cell6=ws.cell(row=current_row+6, column=7, value="Sign & Date: " + ( frappe.utils.formatdate(frappe.utils.today(), 'dd-MM-YYYY')) )
    cell6.font = bold_font
    cell6.border = thin_border
    cell6.alignment = Alignment(horizontal="center")
    
    


    
        
        
        
    xlsx_file = BytesIO()
    wb.save(xlsx_file)
    xlsx_file.seek(0)
    return xlsx_file

