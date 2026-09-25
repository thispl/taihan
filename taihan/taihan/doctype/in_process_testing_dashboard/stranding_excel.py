import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.drawing.image import Image
from io import BytesIO
import frappe
from frappe.utils import formatdate

TOTAL_COLUMNS = 16  # centralize the number of columns the report uses

@frappe.whitelist()
def download_stranding_excel():
    filename = 'Stranding QC Final Test - Single Mode'   # no .xlsx here
    build_xlsx_response(filename)

def build_xlsx_response(filename):
    xlsx_file = make_xlsx(sheet_name=filename)
    frappe.response['filename'] = filename + '.xlsx'
    frappe.response['filecontent'] = xlsx_file.getvalue()
    frappe.response['type'] = 'binary'

def make_xlsx(sheet_name=None):
    args = frappe.local.form_dict
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name if sheet_name else 'Sheet1'

    # Default column widths (small initially, will set final widths later)
    for col in range(1, 26):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 4.5

    # Report Header
    titles = [
        ("C1:P1", "TAIHAN KUWAIT FIBER OPTIC CABLE CO", True, False),
        ("C2:P2", "ISO 9001:2015, ISO 14001:2015, ISO 45001:2018 Management System Certificate", True, False),
        ("C3:P3", "Quality Assurance & Inspection Department", True, False),
        ("C4:P4", "Executive Standard: IEC 60793-1-40", True, False),
        ("C5:P5", "Attenuation Test Results", True, True)
    ]
    for cell_range, text, bold, underline in titles:
        ws.merge_cells(cell_range)
        start_cell = cell_range.split(":")[0]
        ws[start_cell].font = Font(bold=bold, underline="single" if underline else None)
        ws[start_cell].value = text
        ws[start_cell].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # Logo
    ws.merge_cells("A1:B5")
    try:
        img_path = frappe.get_site_path("public", "files", "Taihan Kuwait logo1_page-0001 (1).jpg")
        img = Image(img_path)
        img.width, img.height = 100, 60
        ws.add_image(img, "A2")
    except Exception:
        ws["A2"].value = "[LOGO]"

    # Data (append rows)
    data = get_data(args)
    for row_data in data:
        ws.append(row_data)

    # Predefined merges for header rows
    for row in range(1, 6):
        ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=16)

    # Data row merges (these are structural merges for the first data block)
    for row in range(6, 11):
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
        ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=8)
        ws.merge_cells(start_row=row, start_column=9, end_row=row, end_column=10)
        if row == 9:
            ws.merge_cells(start_row=row, start_column=11, end_row=row, end_column=12)
            ws.merge_cells(start_row=row, start_column=13, end_row=row, end_column=14)
            ws.merge_cells(start_row=row, start_column=15, end_row=row, end_column=16)
        else:
            ws.merge_cells(start_row=row, start_column=11, end_row=row, end_column=16)

    # Re-fetch doc (used later)
    docname = args.get("docname")
    if not docname:
        frappe.throw("Missing 'docname' in request.")
    doc = frappe.get_doc("Quality Inspection", docname)

    # Find dynamic start row for fiber data (first row where column 1 looks like a serial number)
    first_fiber_row = None
    for r in range(1, ws.max_row + 1):
        val = ws.cell(row=r, column=1).value
        if val is not None and str(val).strip().isdigit():
            first_fiber_row = r
            break
    # If we didn't find numeric sl.no, fallback to 8 which is the expected row in the old layout
    if not first_fiber_row:
        first_fiber_row = 8

    # Merge Tube Colour + Remarks (both sides) using the computed start row
    merge_tube_and_remarks(ws, first_fiber_row, 2, 8, ws.max_row)
    merge_tube_and_remarks(ws, first_fiber_row, 10, 16, ws.max_row)

    # If not custom attenuation optional, perform extra merges already present in your script
    if not doc.custom_attenuation_optional:
        ws.merge_cells(start_row=11, start_column=1, end_row=11, end_column=2)
        ws.merge_cells(start_row=11, start_column=3, end_row=11, end_column=4)
        ws.merge_cells(start_row=11, start_column=5, end_row=11, end_column=7)
        ws.merge_cells(start_row=11, start_column=8, end_row=12, end_column=8)
        ws.merge_cells(start_row=11, start_column=9, end_row=11, end_column=10)
        ws.merge_cells(start_row=11, start_column=11, end_row=11, end_column=12)
        ws.merge_cells(start_row=11, start_column=13, end_row=11, end_column=15)
        ws.merge_cells(start_row=11, start_column=16, end_row=12, end_column=16)

    # Add attenuation table
    start_table_row = len(doc.custom_stranding_attenuation or []) // 2 + (10 if doc.custom_attenuation_optional else 13)
    add_attenuation_table(ws, start_table_row, doc)

    # Final column widths
    set_column_widths(ws)

    # Apply styles after everything is placed so merged ranges and full sheet are styled
    apply_styles(ws, TOTAL_COLUMNS)

    # Ensure merged ranges have consistent alignment (apply to start cell is usually enough,
    # but set alignment on every cell of merged region to be safe)
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for merged_range in list(ws.merged_cells.ranges):
        min_row, min_col, max_row, max_col = merged_range.min_row, merged_range.min_col, merged_range.max_row, merged_range.max_col
        for r in range(min_row, max_row + 1):
            for c in range(min_col, max_col + 1):
                ws.cell(row=r, column=c).alignment = center_align

    # Output
    xlsx_file = BytesIO()
    wb.save(xlsx_file)
    xlsx_file.seek(0)
    return xlsx_file

def apply_styles(ws, total_column):
    align_center = Alignment(horizontal='center', vertical='center', wrap_text=True)
    align_left = Alignment(horizontal='left', vertical='top', wrap_text=True)

    header_font = Font(bold=True, size=14)
    text_font_data = Font(size=9)

    thin = Side(border_style='thin')
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    white_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")

    # Header rows (1–5)
    for row in ws.iter_rows(min_row=1, max_row=5, min_col=1, max_col=total_column):
        for cell in row:
            cell.font = header_font
            cell.alignment = align_center
            cell.fill = white_fill
            if cell.row == 1:
                cell.border = Border(left=thin, right=thin, top=thin, bottom=None)
            elif cell.row in [2, 3, 4]:
                cell.border = Border(left=thin, right=thin, top=None, bottom=None)
            elif cell.row == 5:
                cell.border = Border(left=thin, right=thin, top=None, bottom=thin)

    # Body rows - from row 6 to end
    for row in ws.iter_rows(min_row=6, max_row=ws.max_row, min_col=1, max_col=total_column):
        for cell in row:
            if cell.row in [6, 7, 8, 9, 10]:
                cell.alignment = align_left
            else:
                cell.alignment = align_center
            cell.font = text_font_data
            cell.border = border

def set_column_widths(ws):
    # Adjust as you prefer; default kept as 10 wide for many columns for a readable report
    column_widths = [10] * 60
    for i, width in enumerate(column_widths, start=1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width

def get_data(args):
    docname = args.get("docname")
    if not docname:
        frappe.throw("Missing 'docname' in request.")
    doc = frappe.get_doc("Quality Inspection", docname)

    po_no = frappe.db.get_value("Sales Order", {"name": doc.sales_order}, "po_no") if doc.sales_order else ""
    report_date = formatdate(doc.report_date, 'dd-mm-yyyy')

    data = [
        ["Description", "", doc.description, "", "", "", "", "", "Customer", "", doc.custom_customer, "", "", "", "", ""],
        ["Drum Tag No.", "", doc.item_code, "", "", "", "", "", "Reference No.", "", doc.reference_name, "", "", "", "", ""],
        ["Sales Order No.", "", doc.sales_order, "", "", "", "", "", "Refractive Index", "", " ", "", "", "", "", ""],
        ["P.O No.", "", po_no, "", "", "", "", "", "Optical Length (M)", "", doc.custom_optical_length, "", "Physical Length (M)", "", doc.custom_physical_length, ""],
        ["Cable ID", "", doc.custom_cable_id, "", "", "", "", "", "Date of Testing", "", report_date, "", "", "", "", ""],
        ["Loose Tube", "", "Fiber", "", "Attenuation (dB/Km)", "", "", "Remarks", "Loose Tube", "", "Fiber", "", "Attenuation (dB/Km)", "", "", "Remarks"],
        ["SL. No", "Colour", "No", "Colour", "1310 nm", "1550 nm", "1625 nm", "", "SL. No", "Colour", "No", "Colour", "1310 nm", "1550 nm", "1625 nm", ""]
    ]

    if doc.custom_attenuation_optional:
        # If optional, header only (no fiber rows)
        data = [
            ["Description", "", doc.description, "", "", "", "", "", "Customer", "", doc.custom_customer, "", "", "", "", ""],
            ["Drum Tag No.", "", doc.item_code, "", "", "", "", "", "Reference No.", "", doc.reference_name, "", "", "", "", ""],
            ["Sales Order No.", "", doc.sales_order, "", "", "", "", "", "Refractive Index", "", " ", "", "", "", "", ""],
            ["P.O No.", "", po_no, "", "", "", "", "", "Optical Length (M)", "", doc.custom_optical_length, "", "Physical Length (M)", "", doc.custom_physical_length, ""],
            ["Cable ID", "", doc.custom_cable_id, "", "", "", "", "", "Date of Testing", "", formatdate(doc.report_date, 'dd-mm-yyyy'), "", "", "", "", ""],
        ]
    else:
        fibers = doc.custom_stranding_attenuation or []
        if not fibers:
            return data
        half = len(fibers) // 2
        left_side, right_side = fibers[:half], fibers[half:]
        for i in range(half):
            left = left_side[i]
            right = right_side[i] if i < len(right_side) else None
            row = [
                str(i + 1), left.tube_colour, str(left.idx), left.fiber_colour,
                left.attenuation_at_1310_nm, left.attenuation_at_1550_nm, left.attenuation_at_1625_nm or 0, left.remark or "",
            ]
            if right:
                row += [
                    str(i + 1 + half), right.tube_colour, str(right.idx), right.fiber_colour,
                    right.attenuation_at_1310_nm, right.attenuation_at_1550_nm, right.attenuation_at_1625_nm or 0, right.remark or "",
                ]
            data.append(row)
    return data

def merge_tube_and_remarks(ws, start_row, tube_col, remarks_col, total_rows):
    """
    Merge continuous identical values in column `tube_col` and merge the same rows in `remarks_col`.
    start_row should be where the fiber rows start (SL. No row).
    """
    current_value = None
    merge_start = start_row
    for r in range(start_row, total_rows + 1):
        cell_value = ws.cell(row=r, column=tube_col).value
        # treat empty/None as distinct; skip merging None blocks
        if cell_value != current_value:
            # finalize previous block (if more than one row)
            if current_value is not None and (r - merge_start) > 1:
                ws.merge_cells(start_row=merge_start, start_column=tube_col, end_row=r - 1, end_column=tube_col)
                ws.cell(row=merge_start, column=tube_col).alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                ws.merge_cells(start_row=merge_start, start_column=remarks_col, end_row=r - 1, end_column=remarks_col)
                ws.cell(row=merge_start, column=remarks_col).alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            current_value = cell_value
            merge_start = r
    # finalize last block up to total_rows
    if current_value is not None and (total_rows - merge_start + 1) > 1:
        ws.merge_cells(start_row=merge_start, start_column=tube_col, end_row=total_rows, end_column=tube_col)
        ws.cell(row=merge_start, column=tube_col).alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.merge_cells(start_row=merge_start, start_column=remarks_col, end_row=total_rows, end_column=remarks_col)
        ws.cell(row=merge_start, column=remarks_col).alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

def apply_outline_borders(ws, top_row, bottom_row, left_col=1, right_col=16, hide_top=False, hide_bottom=False):
    thin = Side(style="thin")
    for r in range(top_row, bottom_row + 1):
        for c in range(left_col, right_col + 1):
            sides = {}
            if not hide_top and r == top_row:
                sides["top"] = thin
            if not hide_bottom and r == bottom_row:
                sides["bottom"] = thin
            if c == left_col:
                sides["left"] = thin
            if c == right_col:
                sides["right"] = thin
            ws.cell(row=r, column=c).border = Border(**sides)

def apply_full_borders(ws, top_row, bottom_row, left_col=1, right_col=16):
    thin = Side(style="thin")
    for r in range(top_row, bottom_row + 1):
        for c in range(left_col, right_col + 1):
            ws.cell(row=r, column=c).border = Border(left=thin, right=thin, top=thin, bottom=thin)

def add_attenuation_table(ws, start_row, doc):
    header_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left_align = Alignment(horizontal="left", vertical="top", wrap_text=True)
    white_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")

    row = start_row + 1

    # Top Note
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=16)
    ws.cell(row=row, column=1, value="# This report has been generated in laboratory at room temperature.")
    for c in range(1, 17):
        ws.cell(row=row, column=c).fill = white_fill
        ws.cell(row=row, column=c).alignment = left_align
    apply_outline_borders(ws, row, row, 1, 16, hide_bottom=True)
    row += 1

    table_top = row

    if doc.custom_attenuation_optional:
        # Header
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=11)
        ws.merge_cells(start_row=row, start_column=12, end_row=row + 1, end_column=12)
        ws.cell(row=row, column=12, value="Customer Req.")
        ws.cell(row=row, column=13, value="1310 nm")
        ws.cell(row=row, column=14, value="1550 nm")
        ws.cell(row=row, column=15, value="1625 nm")
        apply_outline_borders(ws, table_top, row + 1, 12, 15)
        for r in range(row, row + 2):
            for c in range(12, 16):
                ws.cell(row=r, column=c).fill = header_fill
                ws.cell(row=r, column=c).alignment = center

        # Customer Req values
        row += 1
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=11)
        ws.cell(row=row, column=13, value=" ")
        ws.cell(row=row, column=14, value="")
        ws.cell(row=row, column=15, value=" ")
        for c in range(13, 16):
            ws.cell(row=row, column=c).fill = header_fill
            ws.cell(row=row, column=c).alignment = center
        row += 1

        # Merge remarks column
        ws.merge_cells(start_row=row, start_column=16, end_row=row, end_column=16)

        # Attenuation rows
        for label, atten_type in [("Maximum", "Maximum"), ("Minimum", "Minimum"), ("Average", "Average")]:
            ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=11)
            if label == "Maximum":
                ws.cell(row=row, column=1, value="Note: Attenuation & Continuity OK")
            ws.cell(row=row, column=12, value=label)
            ws.cell(row=row, column=13, value=frappe.db.get_value("Single Attenuation", {"parent": doc.name, "type": atten_type}, "1310_nm"))
            ws.cell(row=row, column=14, value=frappe.db.get_value("Single Attenuation", {"parent": doc.name, "type": atten_type}, "1550_nm"))
            ws.cell(row=row, column=15, value=frappe.db.get_value("Single Attenuation", {"parent": doc.name, "type": atten_type}, "1625_nm"))
            apply_full_borders(ws, row, row, 12, 15)
            row += 1

        table_bottom = row - 1
        apply_outline_borders(ws, table_top, table_bottom, 16, 16)

    # Footer
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
    ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=11)
    ws.merge_cells(start_row=row, start_column=12, end_row=row, end_column=13)
    ws.merge_cells(start_row=row, start_column=14, end_row=row, end_column=16)
    ws.cell(row=row, column=1, value="Tested By:")
    ws.cell(row=row, column=3, value=doc.inspected_by)
    ws.cell(row=row, column=12, value="Verified By:")
    ws.cell(row=row, column=14, value="Chandan Dey (QC Engineer)")
    for c in range(1, 17):
        ws.cell(row=row, column=c).alignment = left_align
    row += 1

    # Address
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=16)
    ws.cell(row=row, column=1, value="Plot No.176 , Block 21 , Mina Abdulla Industrial Area , Al Ahamadi Governorate , Kuwait")
    ws.cell(row=row, column=1).alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    row += 1

    # Website
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=16)
    ws.cell(row=row, column=1, value="Website: www.taihankuwait.com")
    ws.cell(row=row, column=1).alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    apply_outline_borders(ws, row, row, 1, 16, hide_top=True)

    return row + 1
