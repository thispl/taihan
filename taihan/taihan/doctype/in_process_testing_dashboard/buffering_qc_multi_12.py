from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.drawing.image import Image
import frappe, io
import os
from frappe.utils.file_manager import get_file_path
from openpyxl.drawing.spreadsheet_drawing import AnchorMarker, OneCellAnchor
import base64

@frappe.whitelist()
def download_buffering_multi_12_excel(docname):
    doc = frappe.get_doc("Quality Inspection", docname)
    wb = Workbook()
    ws = wb.active
    ws.title = "OTDR Buffering Multi"

    # Styles
    thin = Side(border_style="thin", color="000000")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    center = Alignment(horizontal="center", vertical="center")
    left = Alignment(horizontal="left", vertical="center")
    bold = Font(bold=True)

    file_url = "/files/Taihan Kuwait logo1_page-0001 (1).jpg"   # same as uploaded in ERPNext
    file_path = frappe.get_site_path("public", file_url.lstrip("/"))

    # === Header with Logo & Title ===
    if os.path.exists(file_path):
        img = Image(file_path)
        img.width, img.height = 112, 50
        
        ws.add_image(img,"A1")
    else:
        frappe.throw(f"Logo file not found at {file_path}")
    # for r in range(1, 4):   # till subtitle row
    #     ws.cell(row=r, column=2).border = Border(left=thin)
    # Title
    ws.merge_cells("A1:C3")
    ws["A1"].alignment = left
    
    for r in ws.iter_rows(min_row=1, max_row=3,
                              min_col=1, max_col=3):
            for cell in r:
                cell.border = Border(left=thin, right=thin, top=thin, bottom=thin)
    
    ws.merge_cells("D1:K2")
    ws["D1"] = "TAIHAN KUWAIT FIBER OPTIC CABLE CO"
    ws["D1"].font = Font(bold=True, size=14)
    ws["D1"].alignment = center
    
    for r in ws.iter_rows(min_row=1, max_row=2,
                                min_col=4, max_col=11):
            for cell in r:
                cell.border = Border(left=thin, right=thin, top=thin)

    # Subtitle
    ws.merge_cells("D3:K3")
    ws["D3"] = "OTDR Test Report (2-12F) - Sec. Coating Line"
    ws["D3"].font = Font(size=12)
    ws["D3"].alignment = center
    
    for r in ws.iter_rows(min_row=3, max_row=3,
                                min_col=4, max_col=11):
            for cell in r:
                cell.border = Border(left=thin, right=thin,  bottom=thin)

    # === Border Function ===
    def apply_border_to_range(start_row, start_col, end_row, end_col):
        """Apply border to a merged cell block"""
        for r in ws.iter_rows(min_row=start_row, max_row=end_row,
                              min_col=start_col, max_col=end_col):
            for cell in r:
                cell.border = border
    ws.column_dimensions['A'].width = 18   # Tube Colour
    ws.column_dimensions['B'].width = 11   # Fibre Colour
    ws.column_dimensions['C'].width = 8
    ws.column_dimensions['D'].width = 12
    ws.column_dimensions['E'].width = 10
    ws.column_dimensions['F'].width = 8   # Remark
    ws.column_dimensions['G'].width = 18
    ws.column_dimensions['H'].width = 13
    ws.column_dimensions['I'].width = 13
    ws.column_dimensions['J'].width = 13
    ws.column_dimensions['K'].width = 13

    # === Customer / Fiber Count ===
    row = ws.max_row + 1
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=5)
    ws.cell(row=row, column=1, value=f"Customer:{doc.custom_customer or ''} ")
    
    for r in ws.iter_rows(min_row=4, max_row=4,
                            min_col=1, max_col=5):
        for cell in r:
            cell.border = Border(left=thin,  top=thin, bottom=thin)
    
    ws.merge_cells(start_row=row, start_column=6, end_row=row, end_column=11)
    ws.cell(row=row, column=6, value=f"Fiber count - {doc.custom_fiber_count or 0}F")
    ws.cell(row=row, column=6).alignment = Alignment(horizontal="right", vertical="center")
    for r in ws.iter_rows(min_row=4, max_row=4,
                                min_col=6, max_col=11):
            for cell in r:
                cell.border = Border(right=thin, top=thin, bottom=thin)  
    

    # === Sales Order / Mfg Date / LT ID ===
    row += 1
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=5)
    ws.cell(row=row, column=1, value=f"Sales Order No: {doc.sales_order or ''}")
    apply_border_to_range(row, 1, row, 5)

    ws.merge_cells(start_row=row, start_column=6, end_row=row, end_column=11)
    manu_date = frappe.db.get_value("Job Card", doc.reference_name, "posting_date")
    ws.cell(row=row, column=6, value=f"Mfg. Date: {frappe.utils.formatdate(manu_date) if manu_date else ''}")
    apply_border_to_range(row, 6, row, 7)

    ws.merge_cells(start_row=row, start_column=8, end_row=row, end_column=11)
    # ws.cell(row=row, column=8, value=f"LT ID: {doc.custom_lt_id or ''}")
    apply_border_to_range(row, 8, row, 11)

    # === Machine Operator / Shift Engg ===
    row += 1
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=5)
    ws.cell(row=row, column=1, value=f"Machine Operator Name: {doc.custom_operator or ''}")
    apply_border_to_range(row, 1, row, 5)

    ws.merge_cells(start_row=row, start_column=6, end_row=row, end_column=7)
    ws.cell(row=row, column=6, value="Prod. Shift Engg. Name:")
    apply_border_to_range(row, 6, row, 7)

    ws.merge_cells(start_row=row, start_column=8, end_row=row, end_column=11)
    ws.cell(row=row, column=8, value=f"{doc.custom_production_shift_engineering_name or ''}")
    apply_border_to_range(row, 8, row, 11)

    # === OTDR No / Fiber Type / Bobbin No ===
    row += 1
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=5)
    ws.cell(row=row, column=1, value=f"OTDR No: {doc.custom_otdr_no or ''}")
    apply_border_to_range(row, 1, row, 5)

    ws.merge_cells(start_row=row, start_column=6, end_row=row, end_column=7)
    ws.cell(row=row, column=6, value=f"Fiber Type: {doc.custom_fiber_type or ''}")
    apply_border_to_range(row, 6, row, 7)

    ws.merge_cells(start_row=row, start_column=8, end_row=row, end_column=11)
    ws.cell(row=row, column=8, value=f"Bobbin No: {doc.custom_bobbin_no or ''}")
    apply_border_to_range(row, 8, row, 11)

    for _ in range(2):
        row += 1   
        for col in range(1, 10):
            ws.cell(row=row, column=col, value="")
    ws.merge_cells(start_row=row-1, start_column=1, end_row=row, end_column=1)
    ws.cell(row=row-1, column=1, value="IOR").alignment = Alignment(horizontal="center", vertical="center")
    ws.cell(row=row-1, column=1).border = border        
    
    ws.cell(row=row-1, column=2, value="850nm").border = border
    ws.cell(row=row-1, column=3, value="1300nm").border = border
    ws.cell(row=row-1, column=4, value="").border = border
    for col in range(2, 5):
        ws.cell(row=row-1, column=col).alignment = Alignment(horizontal="center", vertical="center")
    ws.cell(row=row, column=2, value=f"{doc.custom_ior__850_nm or ''}").border = border
    ws.cell(row=row, column=3, value=f"{doc.custom_ior__1300_nm or ''}").border = border
    ws.cell(row=row, column=4, value="").border = border

    for col in range(2, 5):
        ws.cell(row=row, column=col).alignment = Alignment(horizontal="center", vertical="center")
    
    ws.merge_cells(start_row=row-1, start_column=5, end_row=row-1, end_column=7)
    ws.cell(row=row-1, column=5, value=f"Shift: {doc.custom_shift or ''}").border = border
    ws.cell(row=row-1, column=5).alignment = Alignment(horizontal="center", vertical="center")

    ws.merge_cells(start_row=row-1, start_column=8, end_row=row-1, end_column=11)
    ws.cell(row=row-1, column=8, value=f"Prod. Length (M): {doc.custom_production_length or ''}").border = border
    ws.cell(row=row-1, column=8).alignment = Alignment(horizontal="left", vertical="center")

    ws.merge_cells(start_row=row, start_column=5, end_row=row, end_column=7)
    ws.cell(row=row, column=5, value="").border = border
    ws.cell(row=row, column=5).alignment = Alignment(horizontal="center", vertical="center")
    
    ws.merge_cells(start_row=row, start_column=8, end_row=row, end_column=11)
    ws.cell(row=row, column=8, value=f"OTDR Length(M): {doc.custom_otdr_lengthm or ''}").border = border
    ws.cell(row=row, column=8).alignment = Alignment(horizontal="left", vertical="center")


    row += 1
    ws.merge_cells(start_row=row, start_column=1, end_row=row+2, end_column=1)
    ws.cell(row=row, column=1, value="Tube Colour").alignment = center
    ws.cell(row=row, column=1).font = bold

    ws.merge_cells(start_row=row, start_column=2, end_row=row+2, end_column=2)
    ws.cell(row=row, column=2, value="Fiber Colour").alignment = center
    ws.cell(row=row, column=2).font = bold

    ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=4)
    ws.cell(row=row, column=3, value="Attenuation dB/km").alignment = center
    ws.cell(row=row, column=3).font = bold
    ws.cell(row=row+1, column=3, value="850 nm").alignment = center
    ws.cell(row=row+1, column=4, value="1300 nm").alignment = center

    ws.merge_cells(start_row=row, start_column=5, end_row=row, end_column=5)
    ws.cell(row=row, column=5, value="Length").alignment = center
    ws.cell(row=row, column=5).font = bold
    ws.cell(row=row+1, column=5, value="km").alignment = center
    ws.cell(row=row+1, column=5).font = bold
    
    # === Remarks Row ===
    
    ws.merge_cells(start_row=row, start_column=6, end_row=row+2, end_column=8)
    ws.cell(row=row, column=6, value="Remark").alignment = center
    ws.cell(row=row, column=6).font = bold

    # === LT Dimensions Header (2-row merged) ===
    ws.merge_cells(start_row=row, start_column=9, end_row=row+2, end_column=11)
    ws.cell(row=row, column=9, value="LT Dimensions").alignment = center
    ws.cell(row=row, column=9).font = bold

    # === Data Rows with LT Dimensions block aligned ===
    # start_data_row = row + 2
    # for idx, d in enumerate(doc.custom_attenuation):
    #     ws.cell(row=start_data_row+idx, column=1, value=d.tube_colour).border = border
    #     ws.cell(row=start_data_row+idx, column=2, value=d.fiber_colour).border = border
    #     ws.cell(row=start_data_row+idx, column=3, value=d.attenuation_at_1550_nm).border = border
    #     ws.cell(row=start_data_row+idx, column=4, value=d.attenuation_at_1550_nm).border = border
    #     # ws.cell(row=start_data_row+idx, column=5, value=d.attenuation_at_1625_nm).border = border
    #     ws.cell(row=start_data_row+idx, column=5, value=d.remark).border = border
    #     for col in range(1, 7):
    #         ws.cell(row=start_data_row+idx, column=col).alignment = center

    
    
    for _row in ws.iter_rows(min_row=5, max_row=25, min_col=1, max_col=11):
        for cell in _row:
            cell.border = border


    # === Data Rows ===
    start_data_row = row + 3
    for idx, d in enumerate(doc.custom_mm_attenuation):
        current_row = start_data_row + idx

        ws.cell(row=current_row, column=1, value=d.tube_colour).border = border
        ws.cell(row=current_row, column=2, value=d.fiber_colour).border = border
        ws.cell(row=current_row, column=3, value=d.attenuation_at_850_nm).border = border
        ws.cell(row=current_row, column=4, value=d.attenuation_at_1300_nm).border = border
        
        ws.cell(row=current_row, column=5, value="").border = border
        ws.cell(row=current_row, column=5).alignment = center

        # === Merge Remark cols 5 & 6 ===
        if idx == 0:  # Only do for the first group
            ws.merge_cells(start_row=current_row, start_column=6, end_row=24, end_column=8)
            ws.cell(row=current_row, column=6).value = doc.remarks
            ws.cell(row=current_row, column=6).alignment = center
            for r in ws.iter_rows(min_row=current_row, max_row=24, min_col=6, max_col=8):
                for cell in r:
                    cell.border = border
        for col in range(1, 5):
            ws.cell(row=current_row, column=col).alignment = center

    
    
    ws.merge_cells(start_row=13 ,start_column=9, end_row=14, end_column=9  )
    ws.merge_cells(start_row=13 ,start_column=10, end_row=13, end_column=10  )
    ws.merge_cells(start_row=14 ,start_column=10, end_row=14, end_column=10  )
    ws.merge_cells(start_row=13 ,start_column=11, end_row=13, end_column=11  )
    ws.merge_cells(start_row=14 ,start_column=11, end_row=14, end_column=11  )
    
    ws.cell(row=13, column=9, value="LT OD (mm)").border = border
    ws.cell(row=13, column=10, value="Min").alignment=center
    ws.cell(row=13, column=11, value="Max").alignment=center
    ws.cell(row=14, column=10, value=f" {doc.custom_lt_od_min or ''}").alignment=center
    ws.cell(row=14, column=11, value=f" {doc.custom_lt_od_max or ''}").alignment=center

    ws.merge_cells(start_row=15 ,start_column=9, end_row=16, end_column=9  )
    
    
    ws.cell(row=15, column=9, value="ID (mm)").border = border
    ws.merge_cells(start_row=15, start_column=10, end_row=16, end_column=11)
    ws.cell(row=15, column=10, value=f"{doc.custom_id_mm or ''}").border = border
    
    ws.merge_cells(start_row=17 ,start_column=9, end_row=18, end_column=9  )
    ws.merge_cells(start_row=17 ,start_column=10, end_row=17, end_column=10 )
    ws.merge_cells(start_row=18 ,start_column=10, end_row=18, end_column=10 )
    ws.merge_cells(start_row=17 ,start_column=11, end_row=17, end_column=11 )
    ws.merge_cells(start_row=18 ,start_column=11, end_row=18, end_column=11 )

    ws.cell(row=17, column=9, value="Thickness (mm)").border = border
    ws.cell(row=17, column=10, value="Min").alignment=center
    ws.cell(row=17, column=11, value="Max").alignment=center
    ws.cell(row=18, column=10, value=f" {doc.custom_thickness_min or ''}").alignment=center
    ws.cell(row=18, column=11, value=f" {doc.custom_thickness_max or ''}").alignment=center
    
    ws.merge_cells(start_row=19 ,start_column=9, end_row=20, end_column=9  )
    

    ws.cell(row=19, column=9, value="Kink Test").border = border
    ws.merge_cells(start_row=19, start_column=10, end_row=20, end_column=11)
    ws.cell(row= 19 , column=10, value=f"{doc.custom_kink_test or ''}").border = border
    
    ws.merge_cells(start_row=21 ,start_column=9, end_row=21, end_column=9  )
    

    # === Tested By (Row 16) ===
    ws.cell(row=21, column=9, value="Tested By").border = border   # G16
    ws.merge_cells(start_row=21, start_column=10, end_row=21, end_column=11)  # H16:J16
    ws.cell(row=21, column=10, value=f"{doc.inspected_by or ''}").border = border
    
    ws.merge_cells(start_row=22 ,start_column=9, end_row=24, end_column=9  )
    

    # === Sign & Date (Row 17) ===
    ws.cell(row=22, column=9, value="Sign & Date").border = border  # G17
    ws.merge_cells(start_row=22, start_column=10, end_row=24, end_column=11)  # H17:J17
    
    
    

    

    # === Merge Tube Colour & Remarks column (after header) 12 rows group ===
    total_rows = len(doc.custom_attenuation)
    frappe.log_error(message= total_rows,title="Total Rows")
    frappe.log_error(message= len(doc.custom_attenuation),title="custom_attenuation")
    start_row_idx = start_data_row   # first data row (header ku next row)
    group_size = 12

    for i in range(0, total_rows, group_size):
        start = start_row_idx + i
        end = min(start + group_size - 1, start_row_idx + total_rows - 1)

        # === Tube Colour merge (col=1) ===
        ws.merge_cells(start_row=start, start_column=1, end_row=end, end_column=1)
        ws.cell(row=start, column=1).alignment = center
        ws.cell(row=start, column=1).border = border
        for r in ws.iter_rows(min_row=start, max_row=end, min_col=1, max_col=1):
            for cell in r:
                cell.border = border

        # # === Remark merge (col=5 & 6) ===
        # ws.merge_cells(start_row=start, start_column=6, end_row=24, end_column=8)
        # # ws.cell(row=start, column=6).alignment = center
        # # ws.cell(row=start, column=6).border = border
        # # for r in ws.iter_rows(min_row=start, max_row=end, min_col=6, max_col=8):
        # #     for cell in r:
        # #         cell.border = border
        # ws.merge_cells(start_row=13,start_column=6, end_row=24, end_column=8)        
        
        
        if i == 0:  # Only do for the first group
            ws.merge_cells(start_row=start, start_column=6, end_row=end, end_column=8)
            ws.cell(row=start, column=6)
            ws.cell(row=start, column=6).alignment = center
            for r in ws.iter_rows(min_row=start, max_row=end, min_col=6, max_col=8):
                for cell in r:
                    cell.border = border


    # Apply border + alignment
    for r in ws.iter_rows(min_row=12, max_row=17, min_col=7, max_col=9):
        for cell in r:
            cell.alignment = center
            cell.border = border


    # === Footer ===
    row = ws.max_row + 1   

    # First block (A–C)
    ws.merge_cells(start_row=25, start_column=1, end_row=row, end_column=3)
    ws.cell(row=25, column=1, value=f"Doc No. {doc.name}").alignment = center
    ws.cell(row=25, column=1).border = border

    # Second block (D–F)
    ws.merge_cells(start_row=25, start_column=4, end_row=row, end_column=8)
    ws.cell(row=25, column=4, value=f"Rev.No:0/1").alignment = center
    ws.cell(row=25, column=4).border = border
    # === Merge G8:I35 ===
    # ws.merge_cells(start_row=18, start_column=7, end_row=35, end_column=9)
    # ws.cell(row=18, column=7, value="").border = border
    # ws.cell(row=18, column=7).alignment = center

    # apply border to the merged area
    # for r in ws.iter_rows(min_row=18, max_row=35, min_col=7, max_col=9):
    #     for cell in r:
    #         cell.border = border

    # Third block (G–I)
    ws.merge_cells(start_row=25, start_column=9, end_row=row, end_column=11)
    ws.cell(row=25, column=9, value="Rev. Date: 4-Aug-2024").alignment = center
    ws.cell(row=25, column=9).border = border
    # for cell in ws[ws.max_row]:
    #     cell.border = border
    # max_r = ws.max_row
    # max_c = ws.max_column
    # for r in ws.iter_rows(min_row=1, max_row=max_r, min_col=1, max_col=max_c):
    #     for cell in r:
    #         cell.border = border

    # === Save File to File Doctype and return URL ===
    file_data = io.BytesIO()
    wb.save(file_data)
    file_data.seek(0)

    encoded = base64.b64encode(file_data.getvalue()).decode()
    filename = f"{docname}.xlsx"
    return {"filename": filename, "data": encoded}