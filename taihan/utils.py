import frappe
from frappe.model.naming import make_autoname
from frappe.utils import nowdate

@frappe.whitelist()
def autoname_quotation(doc, method):
    if doc.is_new() and not doc.amended_from:
        company_code = frappe.db.get_value("Company", doc.company, "abbr")
        month = nowdate().split('-')[1]
        year = nowdate().split('-')[0][-2:]
        series = f"{company_code}/{month}-{year}/."
        number = make_autoname(series + "#####")
        seq = number.split("/")[-1]

        # Normal: TKFO/12-24/122EJ
        doc.custom_quotation_name = f"{company_code}/{month}-{year}/{seq}{doc.custom_sales_person_short_code}"

    elif doc.is_new() and doc.amended_from:
        old_name = doc.amended_from.strip()
        short_code = doc.custom_sales_person_short_code

        # Always remove short code from end if present
        if short_code and old_name.endswith(short_code):
            base = old_name[:-len(short_code)]
        else:
            base = old_name

        # Add or increment amendment number
        if "-" in base and base.split("-")[-1].isdigit():
            base_root = "-".join(base.split("-")[:-1])
            num = int(base.split("-")[-1]) + 1
            new_base = f"{base_root}-{num}"
        else:
            new_base = f"{base}-1"

        frappe.errprint(f"{new_base}{short_code}")
        
        doc.custom_quotation_name = f"{new_base}{short_code}"
        doc.name = f"{new_base}{short_code}"
        
@frappe.whitelist()
def update_quotation_series(doc, method):
    if doc.amended_from and doc.custom_quotation_name:
        old_name = doc.amended_from.strip()
        short_code = doc.custom_sales_person_short_code

        # Always remove short code from end if present
        if short_code and old_name.endswith(short_code):
            base = old_name[:-len(short_code)]
        else:
            base = old_name

        # Add or increment amendment number
        if "-" in base and base.split("-")[-1].isdigit():
            base_root = "-".join(base.split("-")[:-1])
            num = int(base.split("-")[-1]) + 1
            new_base = f"{base_root}-{num}"
        else:
            new_base = f"{base}1"
        frappe.rename_doc("Quotation", doc.name,  f"{new_base}{short_code}", force=True)
        doc.name = f"{new_base}{short_code}"


import frappe
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.drawing.image import Image
import io
from itertools import groupby
from datetime import datetime
from openpyxl.utils import get_column_letter
@frappe.whitelist()
def download_attenuation_excel(docname):
    doc = frappe.get_doc("Quality Inspection", docname)
    wb = Workbook()
    ws = wb.active
    ws.title = "Attenuation Test Results"

    # --- Styles ---
    thin = Side(style='thin', color="000000")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left_align = Alignment(horizontal="left", vertical="center")
    blue_fill = PatternFill(start_color="79a8c6", end_color="79a8c6", fill_type="solid")

    # --- Column widths ---
    for col in range(1, 26):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 4.5

    # --- Header logo ---
    ws.merge_cells("A1:C5")
    try:
        img_path = frappe.get_site_path("public", "files", "Taihan Kuwait logo1_page-0001 (1).jpg")
        img = Image(img_path)
        img.width, img.height = 100, 60
        ws.add_image(img, "A1")
    except:
        ws["A1"].value = "[LOGO]"

    # --- Titles ---
    titles = [
        ("D1:N1", "TAIHAN KUWAIT FIBER OPTIC CABLE CO", True),
        ("D2:N2", "ISO 9001:2015, ISO 14001:2015, ISO 45001:2018 Management System Certificate", False),
        ("D3:N3", "Quality Assurance & Inspection Department", True),
        ("D4:N4", "Executive Standard: IEC 60793-1-40", True),
        ("D5:N5", "Attenuation Test Results", True)
    ]
    for rng, txt, bold in titles:
        ws.merge_cells(rng)
        c = ws[rng.split(":")[0]]
        c.value = txt
        c.alignment = center
        c.font = Font(bold=bold, size=12 if "D1" in rng else 11)

    row = 7
    po_no = frappe.db.get_value("Sales Order", {"name": doc.sales_order}, "po_no")

    # Format date as dd-mm-yyyy
    formatted_date = ""
    if doc.report_date:
        try:
            formatted_date = datetime.strptime(str(doc.report_date), "%Y-%m-%d").strftime("%d-%m-%Y")
        except:
            formatted_date = str(doc.report_date)

    # --- Info rows ---
    info_data = [
        ("Description", doc.custom_ft_description),
        ("Drum Tag No.", doc.custom_drum_tag_no),
        ("Sales Order No.", doc.sales_order),
        ("P.O No.", po_no),
        ("Cable ID", doc.custom_cable_id),
        ("Customer", doc.custom_customer),
        ("Reference No.", doc.custom_reference_no),
        ("Refractive Index", "1.466 (1310nm) / 1.467 (1550nm)"),
        ("Optical Length (M)", doc.custom_optical_length, "Physical Length (M)", doc.custom_physical_length),
        ("Date of Testing", formatted_date)
    ]

    total_rows = len(info_data)
    half = total_rows // 2
    left_info = info_data[:half]
    right_info = info_data[half:]

    # --- Write left info (cols 1-6) ---
    for entry in left_info:
        if len(entry) == 4:
            opt_label, opt_value, phy_label, phy_value = entry

            ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
            ws.cell(row=row, column=1, value=opt_label).alignment = center
            ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=4)
            ws.cell(row=row, column=3, value=opt_value).alignment = left_align
            for c in range(1, 5):
                ws.cell(row=row, column=c).border = border

            ws.cell(row=row, column=5, value=phy_label).alignment = center
            ws.cell(row=row, column=5).border = border
            ws.cell(row=row, column=6, value=phy_value).alignment = left_align
            ws.cell(row=row, column=6).border = border

        else:
            label, value = entry
            ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
            ws.cell(row=row, column=1, value=label).alignment = center
            ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=6)
            ws.cell(row=row, column=3, value=value).alignment = left_align
            for c in range(1, 7):
                ws.cell(row=row, column=c).border = border
        row += 1

    # --- Write right info (cols 7-14) ---
    row_right = row - len(left_info)
    for entry in right_info:
        if len(entry) == 4:
            opt_label, opt_value, phy_label, phy_value = entry

            ws.merge_cells(start_row=row_right, start_column=7, end_row=row_right, end_column=8)
            ws.cell(row=row_right, column=7, value=opt_label).alignment = center
            ws.merge_cells(start_row=row_right, start_column=9, end_row=row_right, end_column=10)
            ws.cell(row=row_right, column=9, value=opt_value).alignment = left_align
            for c in range(7, 11):
                ws.cell(row=row_right, column=c).border = border

            ws.merge_cells(start_row=row_right, start_column=11, end_row=row_right, end_column=12)
            ws.cell(row=row_right, column=11, value=phy_label).alignment = center
            ws.merge_cells(start_row=row_right, start_column=13, end_row=row_right, end_column=14)
            ws.cell(row=row_right, column=13, value=phy_value).alignment = left_align
            for c in range(11, 15):
                ws.cell(row=row_right, column=c).border = border

        else:
            label, value = entry
            ws.merge_cells(start_row=row_right, start_column=7, end_row=row_right, end_column=9)
            ws.cell(row=row_right, column=7, value=label).alignment = center
            ws.merge_cells(start_row=row_right, start_column=10, end_row=row_right, end_column=14)
            ws.cell(row=row_right, column=10, value=value).alignment = left_align
            for c in range(7, 15):
                ws.cell(row=row_right, column=c).border = border
        row_right += 1

    row = max(row, row_right)

    # --- Attenuation Table Header ---
    for base_col in [1, 8]:
        ws.merge_cells(start_row=row, start_column=base_col, end_row=row, end_column=base_col+1)
        ws.cell(row=row, column=base_col, value="Loose Tube").alignment = center
        ws.merge_cells(start_row=row, start_column=base_col+2, end_row=row, end_column=base_col+3)
        ws.cell(row=row, column=base_col+2, value="Fiber").alignment = center
        ws.merge_cells(start_row=row, start_column=base_col+4, end_row=row, end_column=base_col+5)
        ws.cell(row=row, column=base_col+4, value="Attenuation (dB/Km)").alignment = center
        ws.merge_cells(start_row=row, start_column=base_col+6, end_row=row, end_column=base_col+6)
        ws.cell(row=row, column=base_col+6, value="").alignment = center
        for i in range(7):
            ws.cell(row=row, column=base_col+i).border = border
            ws.cell(row=row+1, column=base_col+i).border = border
        sub_headers = ["SL. No", "Colour", "No", "Colour", "850 nm", "1300 nm", "Remarks"]
        for i, h in enumerate(sub_headers):
            ws.cell(row=row+1, column=base_col+i, value=h).alignment = center
            ws.cell(row=row+1, column=base_col+i).border = border

    row += 2
    column_widths = {
    1: 6,    # SL. No
    2: 12,   # Tube Colour
    3: 6,    # No
    4: 12,   # Fiber Colour
    5: 12,   # 1310nm
    6: 12,   # 1550nm
    7: 25,   # Remarks (wider)
    8: 6,    # SL. No (Right Table)
    9: 12,   # Tube Colour
    10: 6,   # No
    11: 12,  # Fiber Colour
    12: 12,  # 1310nm
    13: 12,  # 1550nm
    14: 25   # Remarks (Right)
}
    for col, width in column_widths.items():
        ws.column_dimensions[get_column_letter(col)].width = width
    # --- Attenuation Data ---
    if doc.quality_inspection_template == "Stranding QC":
        attenuation = doc.custom_mm_stranding_attenuation or []
    elif doc.quality_inspection_template == "Jacketing QC":
        attenuation = doc.custom_mm_jacketing_attenuation or []
    else:
        attenuation = doc.custom_mm_attenuation or []
    attenuation.sort(key=lambda x: x.tube_colour)
    groups = [list(g) for k, g in groupby(attenuation, key=lambda x: x.tube_colour)]
    half = (len(groups)+1)//2
    left_data = [item for g in groups[:half] for item in g]
    right_data = [item for g in groups[half:] for item in g]

    s_no = 1
    all_1310 = []
    all_1550 = []

    def write_side(data, base_col, serial_start):
        current_row = row
        serial = serial_start
        i = 0
        while i < len(data):
            color = data[i].tube_colour
            same_color_rows = [x for x in data[i:] if x.tube_colour == color]
            merge_count = len(same_color_rows)
            no_count = 1
            if merge_count > 1:
                ws.merge_cells(start_row=current_row, start_column=base_col+1,
                               end_row=current_row+merge_count-1, end_column=base_col+1)
                ws.merge_cells(start_row=current_row, start_column=base_col+6,
                               end_row=current_row+merge_count-1, end_column=base_col+6)
            for j, r in enumerate(same_color_rows):
                ws.cell(row=current_row+j, column=base_col, value=serial).alignment = center
                ws.cell(row=current_row+j, column=base_col).border = border

                ws.cell(row=current_row+j, column=base_col+1,
                        value=r.tube_colour if j == 0 else None).alignment = center
                ws.cell(row=current_row+j, column=base_col+1).border = border

                ws.cell(row=current_row+j, column=base_col+2, value=no_count).alignment = center
                ws.cell(row=current_row+j, column=base_col+2).border = border

                ws.cell(row=current_row+j, column=base_col+3, value=r.fiber_colour).alignment = center
                ws.cell(row=current_row+j, column=base_col+3).border = border

                ws.cell(row=current_row+j, column=base_col+4, value=r.attenuation_at_850_nm).alignment = center
                ws.cell(row=current_row+j, column=base_col+4).border = border

                ws.cell(row=current_row+j, column=base_col+5, value=r.attenuation_at_1300_nm).alignment = center
                ws.cell(row=current_row+j, column=base_col+5).border = border

                ws.cell(row=current_row+j, column=base_col+6,
                        value=doc.remarks if j == 0 else None).alignment = center
                ws.cell(row=current_row+j, column=base_col+6).border = border

                if r.attenuation_at_850_nm:
                    all_1310.append(float(r.attenuation_at_850_nm))
                if r.attenuation_at_1300_nm:
                    all_1550.append(float(r.attenuation_at_1300_nm))

                serial += 1
                no_count += 1
            i += merge_count
            current_row += merge_count
        return current_row, serial

    left_end, next_s_no = write_side(left_data, 1, s_no)
    right_end, _ = write_side(right_data, 8, next_s_no)
    row = max(left_end, right_end)

    max_1310 = max(all_1310) if all_1310 else 0
    min_1310 = min(all_1310) if all_1310 else 0
    max_1550 = max(all_1550) if all_1550 else 0
    min_1550 = min(all_1550) if all_1550 else 0
    avg_1310 = round((max_1310 + min_1310) / 2, 3)
    avg_1550 = round((max_1550 + min_1550) / 2, 3)
    row += 1
    customer_req_start_row = row
    customer_req_rows = 5
    ws.merge_cells(start_row=customer_req_start_row,
                   start_column=1, end_row=customer_req_start_row+customer_req_rows-1, end_column=7)
    ws.cell(row=customer_req_start_row, column=1,
            value="# This report has been generated in laboratory at room temperature.\nNote: Attenuation & Continuity OK").alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    ws.merge_cells(start_row=row, start_column=8, end_row=row, end_column=10)
    ws.cell(row=row, column=8, value="Customer Req.").alignment = center
    ws.merge_cells(start_row=row, start_column=11, end_row=row, end_column=12)
    ws.cell(row=row, column=11, value="1310 nm").alignment = center
    ws.merge_cells(start_row=row, start_column=13, end_row=row, end_column=14)
    ws.cell(row=row, column=13, value="1550 nm").alignment = center

    header_row = row  # store for merging
    row += 1
    # Merge left "Customer Req." header with this value row
    ws.merge_cells(start_row=header_row, start_column=8, end_row=row, end_column=10)
    # Value row
    ws.merge_cells(start_row=row, start_column=11, end_row=row, end_column=12)
    ws.cell(row=row, column=11, value="0.35 dB/Km").alignment = center
    ws.merge_cells(start_row=row, start_column=13, end_row=row, end_column=14)
    ws.cell(row=row, column=13, value="0.22 dB/Km").alignment = center

    # Apply blue background to the merged value row
    for col in range(8, 15):
        ws.cell(row=row, column=col).fill = blue_fill
        ws.cell(row=row, column=col).border = border
        ws.cell(header_row, col).fill = blue_fill  # also apply to header merge
        ws.cell(header_row, col).border = border

    # === Max, Min, Avg rows ===
    # --- Customer Req + Max/Min/Avg ---
    row += 1
    ws.merge_cells(start_row=row, start_column=8, end_row=row, end_column=10)
    ws.cell(row=row, column=8, value="Maximum").alignment = center
    ws.merge_cells(start_row=row, start_column=11, end_row=row, end_column=12)
    ws.cell(row=row, column=11, value=max_1310).alignment = center
    ws.merge_cells(start_row=row, start_column=13, end_row=row, end_column=14)
    ws.cell(row=row, column=13, value=max_1550).alignment = center

    row += 1
    ws.merge_cells(start_row=row, start_column=8, end_row=row, end_column=10)
    ws.cell(row=row, column=8, value="Minimum").alignment = center
    ws.merge_cells(start_row=row, start_column=11, end_row=row, end_column=12)
    ws.cell(row=row, column=11, value=min_1310).alignment = center
    ws.merge_cells(start_row=row, start_column=13, end_row=row, end_column=14)
    ws.cell(row=row, column=13, value=min_1550).alignment = center

    row += 1
    ws.merge_cells(start_row=row, start_column=8, end_row=row, end_column=10)
    ws.cell(row=row, column=8, value="Average").alignment = center
    ws.merge_cells(start_row=row, start_column=11, end_row=row, end_column=12)
    ws.cell(row=row, column=11, value=avg_1310).alignment = center
    ws.merge_cells(start_row=row, start_column=13, end_row=row, end_column=14)
    ws.cell(row=row, column=13, value=avg_1550).alignment = center
    for r in range(row-4, row+1):
        for c in range(8,15):
            ws.cell(r,c).border = border
    row += 1
    
    row += 1
    # === Tested By / Verified By ===
    tested_by = getattr(doc, "custom_tested_by", "") or ""
    verified_by = getattr(doc, "custom_verified_by", "") or ""

    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=7)
    ws.cell(row=row, column=1, value=f"Tested By: {tested_by}").alignment = left_align

    ws.merge_cells(start_row=row, start_column=8, end_row=row, end_column=14)
    ws.cell(row=row, column=8, value=f"Verified By: {verified_by}").alignment = left_align

    # optionally draw borders across the merged cells so they look consistent
    for c in range(1, 15):
        ws.cell(row, c).border = border

    row += 1

    # === Address & Website ===
    row += 1
    # ws.merge_cells(start_row=row,start_column=1,end_row=row,end_column=14)
    # ws.cell(row=row,column=1,value="Plot No.176 , Block 21 , Mina Abdulla Industrial Area , Al Ahamadi Governorate , Kuwait").alignment=center
    # row += 1
    # ws.merge_cells(start_row=row,start_column=1,end_row=row,end_column=14)
    # ws.cell(row=row,column=1,value="Website: www.taihankuwait.com").alignment=center
    # First row: Address
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin")
    )

    ws.merge_cells(start_row=row, start_column=1, end_row=row+1, end_column=14)
    ws.cell(row=row, column=1, value="Plot No.176 , Block 21 , Mina Abdulla Industrial Area , Al Ahamadi Governorate , Kuwait\nWebsite: www.taihankuwait.com").alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for r in range(row, row+2):  # two rows
        for c in range(1, 15):  # columns 1 to 14
            ws.cell(row=r, column=c).border = thin_border

    row += 2


    # Sa    ve Excel
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    frappe.response["filename"] = f"Attenuation_Test_{docname}.xlsx"
    frappe.response["filecontent"] = output.getvalue()
    frappe.response["type"] = "binary"


def autoname_batch(doc, method=None):
    if not doc.is_new() or doc.batch_id:
        return

    naming_series = doc.get("naming_series")
    if not naming_series:
        return

    date_vars = {"YY", "YYYY", "MM", "DD", "WW", "timestamp"}
    parts = [p for p in naming_series.split(".") if p]

    process_code = None
    counter_part = None
    for i, p in enumerate(parts):
        if p and all(c == "#" for c in p):
            counter_part = p
            for j in range(i - 1, -1, -1):
                if parts[j] not in date_vars and not all(c == "#" for c in parts[j]):
                    process_code = parts[j]
                    break
            break

    if not process_code or not counter_part:
        return

    date = nowdate()
    year_short = date[2:4]
    month = date[5:7]

    counter_series = f"{year_short}-{process_code}-.{counter_part}"
    counter_name = make_autoname(counter_series, doc=doc)
    number = counter_name.replace(f"{year_short}-{process_code}-", "")

    doc.batch_id = f"{year_short}.{month}.{process_code}.{number}"
    doc.name = doc.batch_id
