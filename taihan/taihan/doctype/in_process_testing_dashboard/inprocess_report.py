import frappe
import pandas as pd
from frappe.utils import get_site_path, now_datetime
from werkzeug.utils import secure_filename
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.styles import Border, Side

@frappe.whitelist()
def download_excel():
    args = frappe.local.form_dict
    date = args.get("date")
    to_date=args.get("to_date")
    file_name = "In_Process_Testing_Report.xlsx"
    file_path = get_site_path("private", "files", secure_filename(file_name))
   
    df1 = get_coloring_data(date,to_date)
    df2 = get_sec_caoting_data(date,to_date)
    df3=get_stranding_data(date,to_date)
    df4=get_sheathing_data(date,to_date)
    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        df1.to_excel(writer, sheet_name="Coloring", index=False)
        df2.to_excel(writer, sheet_name="Sec. Coating", index=False)
        df3.to_excel(writer, sheet_name="Stranding", index=False)
        df4.to_excel(writer, sheet_name="Sheathing", index=False)
        writer._save()
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    # Load and format the Excel file
    workbook = load_workbook(file_path)
    header_fill = PatternFill(start_color="FF0070C0", end_color="FF0070C0", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    column_widths = {
        "A": 10, "B": 15, "C": 15, "D": 15,
        "E": 15, "F": 15, "G": 15, "H": 15,"I":15,"J":15,"K":15,"L":15,"M":15,"N":15,"O":15,"P":15,"Q":15,
        "R":15,"S":15,"T":15,"U":15,"V":15,"W":15,"X":15
            }

    for sheet_name in workbook.sheetnames:
        ws = workbook[sheet_name]
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.border = thin_border
        for row in ws.iter_rows():
            for cell in row:
                cell.border = thin_border  
        for col, width in column_widths.items():
            ws.column_dimensions[col].width = width

    workbook.save(file_path)
    workbook.close()

    with open(file_path, "rb") as f:
        file_content = f.read()

    return {
        "filename": file_name,
        "content": file_content
    }
    

def get_coloring_data(date,to_date):
    columns = [
        "Date", "Fiber supplier Name", "PO No.", "Color", "Colored Fiber ID ",
        "Fiber Grade", " Length(Km)", "OTDR Length(Km)", "1310nm Actual",
        "1550nm Actual", "1625nm Actual", "Rub Test", "Winding",
        "Testing Operator", "Shift", "Non Conformance Type",
        "Non Conformance Details", "Status"
    ]

    query = """
        SELECT `testing_date`, `fiber_supplier_name`, `po_date`, `color`, `colored_fiber_id`, `fiber_grade`, `length_km`, 
               `otdr_length__km` as otdr_length_km, `color1nm_actual`, `color1550nm_actual`, `color1625nm_actual`, `rub_test`, `winding`, 
               `testing_operator`, `shift`, `non_conformance_type`, `non_conformance_details`, `status`
        FROM `tabInprocess Testing Report`
        WHERE testing_date BETWEEN %s AND %s
    """
    results = frappe.db.sql(query, (date,to_date), as_dict=True) or []

    data = []
    for row in results:
        formatted_date = row.get("testing_date").strftime("%d-%m-%Y") if row.get("testing_date") else ""
        data.append([
            formatted_date,
            row.get("fiber_supplier_name"),
            row.get("po_date"),
            row.get("color"),
            row.get("colored_fiber_id"),
            row.get("fiber_grade"),
            row.get("length_km"),
            row.get("otdr_length_km"),
            row.get("1310nm_actual"),
            row.get("1550nm_actual"),
            row.get("1625nm_actual"),
            row.get("rub_test"),
            row.get("winding"),
            row.get("testing_operator"),
            row.get("shift"),
            row.get("non_conformance_type"),
            row.get("non_conformance_details"),
            row.get("status"),
        ])

    return pd.DataFrame(data, columns=columns)

def get_sec_caoting_data(date,to_date):
    columns = [
       "Date","Customer","Sales Order No.","Fiber Count","Colour or Description","Loose tube ID ","Bobbin No",
        "Prod Length (Mtr)","Otdr Length (Mtr)","Fiber Type","Tube OD (mm)-Min","Tube OD (mm)-Max","Tube ID  (mm)","Tube Thick  Min (mm)",
        "Tube Thick  Max (mm)","Concentricty >90%","Testing Operator","Shift","Non Conformance Type","Non Conformance Details","Status"
    ]

    query = """
        SELECT `testing_date`, `customer`, `sales_order`, `fiber_count`, `colour_or_description`, `loose_tube_id`, `sec_bobbin_no`, 
               `sec_prod_length`, `sec_otdr_length`, `sec_fiber_type`, `sec_tube_od_min`, `sec_tube_od_max`, `sec_tube_id_mm`, 
               `sec_tube_thick_min`, `sec_tube_thick_max`, `sec_concen`, `sec_testing_operator`, `sec_shift`,`sec_non_conformance`,
               `sec_non_conformance_setails`,`sec_staatus`
        FROM `tabInprocess Testing Report`
        WHERE testing_date BETWEEN %s AND %s AND operation_name="Buffering"
    """
    results = frappe.db.sql(query, (date,to_date), as_dict=True) or []

    data = []
    for row in results:
        formatted_date = row.get("testing_date").strftime("%d-%m-%Y") if row.get("testing_date") else ""
        data.append([
            formatted_date,
            row.get("customer"),
            row.get("sales_order"),
            row.get("fiber_count"),
            row.get("colour_or_description"),
            row.get("loose_tube_id"),
            row.get("sec_bobbin_no"),
            row.get("sec_prod_length"),
            row.get("sec_otdr_length"),
            row.get("sec_fiber_type"),
            row.get("sec_tube_od_min"),
            row.get("sec_tube_od_max"),
            row.get("sec_tube_id_mm"),
            row.get("sec_tube_thick_min"),
            row.get("sec_tube_thick_max"),
            round(row.get("sec_concen"),2),
            row.get("sec_testing_operator"),
            row.get("sec_shift"),
            row.get("sec_non_conformance"),
            row.get("sec_non_conformance_setails"),
            row.get("sec_staatus"),
        ])

    return pd.DataFrame(data, columns=columns)

def get_stranding_data(date,to_date):
    columns = [
      "Date","Customer","Sales Order No.","Fiber Count","Core Description","Core ID","Drum No","Prod Length ( MTR)",
        "OTDR Length  ( Mtr)","Core OD (mm)","WBT Size  (mm)","FRP OD (mm)","Testing Operator","Shift","Non Conformance Type",
        "Non Conformance Details","Status"
    ]

    query = """
        SELECT `testing_date`, `customer`, `sales_order`, `stranding_fiber_count`, `core__description`, `core_id`, `drum_no`, 
               `strand_pod_length`, `strand_otdr_length`, `core_od_mm`, `wbt_size__mm`, `frp_od_mm`, `strand_testing_operator`, 
               `starnd_shift`, `strand_non_conformance_type`, `strand_non_conformance_details`, `strand_status`
        FROM `tabInprocess Testing Report`
        WHERE testing_date BETWEEN %s AND %s AND operation_name="Stranding"
    """
    results = frappe.db.sql(query, (date,to_date), as_dict=True) or []

    data = []
    for row in results:
        formatted_date = row.get("testing_date").strftime("%d-%m-%Y") if row.get("testing_date") else ""
        data.append([
            formatted_date,
            row.get("customer"),
            row.get("sales_order"),
            row.get("stranding_fiber_count"),
            row.get("core__description"),
            row.get("core_id"),
            row.get("drum_no"),
            row.get("strand_pod_length"),
            row.get("strand_otdr_length"),
            row.get("core_od_mm"),
            row.get("wbt_size__mm"),
            row.get("frp_od_mm"),
            row.get("strand_testing_operator"),
            row.get("starnd_shift"),
            # row.get("sec_shift"),
            row.get("strand_non_conformance_type"),
            row.get("strand_non_conformance_details"),
            row.get("strand_status"),
        ])

    return pd.DataFrame(data, columns=columns)

def get_sheathing_data(date,to_date):
    columns = [
     "Date","Customer","Sales Order No.","Fiber Count","Cable Description","Sheathing ID","Drum No.","Fiber Type",
        "Inner End (Bottom)","Outer End (Top)","Prod Length (Mtr)","Otdr Length (Mtr)","EFL","Cable OD Min","Cable OD Max","Ovality in (<3%)",
        "Cable Thick  Min (MM)","Cable Thick Max (MM)","Concentricty (>90%)","Testing Operator","Shift","Non Conformance Type",
        "Non Conformance Details","Status" 
    ]

    query = """
        SELECT `testing_date`, `customer`, `sales_order`, `sheathing_fiber_count`, `cable_description`, `sheathing_id`, `sheathing_drumn_no`, 
               `sheathing_fiber_type`, `inner_end_bottom`, `outer_end_top`, `sheathing_prod_length`, `sheathing_otdr_length`, `efl`, 
               `sheathing_cable_od_min`,`sheathing_cable_od_max`, `ovality_in_3`,`sheathing_cable_thick_min`, `sheathing_cable_thick_max`, `sheathing_concentricty`,`sheathing_testing_operator`,
               `sheathing_shift`,`sheathing_non_conformance_type`,`sheathing_non_conformace_details`,`sheathing_status`
        FROM `tabInprocess Testing Report`
        WHERE testing_date BETWEEN %s AND %s AND operation_name="Jacketing"
    """
    results = frappe.db.sql(query, (date,to_date), as_dict=True) or []

    data = []
    for row in results:
        formatted_date = row.get("testing_date").strftime("%d-%m-%Y") if row.get("testing_date") else ""
        value = row.get("sheathing_concentricty")
        data.append([
            formatted_date,
            row.get("customer"),
            row.get("sales_order"),
            row.get("sheathing_fiber_count"),
            row.get("cable_description"),
            row.get("sheathing_id"),
            row.get("sheathing_drumn_no"),
            row.get("sheathing_fiber_type"),
            row.get("inner_end_bottom"),
            row.get("outer_end_top"),
            row.get("sheathing_prod_length"),
            row.get("sheathing_otdr_length"),
            row.get("efl"),
            row.get("sheathing_cable_od_min"),
            row.get("sheathing_cable_od_max"),
            row.get("ovality_in_3"),
            row.get("sheathing_cable_thick_min"),
            row.get("sheathing_cable_thick_max"),
            round(float(value if value is not None else 0), 2),
            row.get("sheathing_testing_operator"),
            row.get("sheathing_shift"),
            row.get("sheathing_non_conformance_type"),
            row.get("sheathing_non_conformace_details"),
            row.get("sheathing_status"),
        ])

    return pd.DataFrame(data, columns=columns)
