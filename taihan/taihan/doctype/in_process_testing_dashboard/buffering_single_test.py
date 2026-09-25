import frappe
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.drawing.image import Image
import io
from datetime import datetime
from openpyxl.utils import get_column_letter

@frappe.whitelist()
def download_attenuation_excel(docname):
	doc = frappe.get_doc("Quality Inspection", docname)
	wb = Workbook()
	ws = wb.active
	ws.title = "Buffering Single Mode Final"

	# --- Styles ---
	thin = Side(style='thin', color="000000")
	border = Border(left=thin, right=thin, top=thin, bottom=thin)
	center = Alignment(horizontal="center", vertical="center", wrap_text=True)
	left_align = Alignment(horizontal="left", vertical="center")
	blue_fill = PatternFill(start_color="79a8c6", end_color="79a8c6", fill_type="solid")

	# --- Column widths ---
	for col in range(1, 26):
		ws.column_dimensions[get_column_letter(col)].width = 4.5

	# --- Header logo ---
	ws.merge_cells("A1:C5")
	try:
		img_path = frappe.get_site_path("public", "files", "Taihan Kuwait logo1_page-0001 (1).jpg")
		img = Image(img_path)
		img.width, img.height = 100, 60
		ws.add_image(img, "A1")
	except:
		ws["B2"].value = "[LOGO]"

	# --- Titles ---
	titles = [
		("D1:P1", "TAIHAN KUWAIT FIBER OPTIC CABLE CO", True),
		("D2:P2", "Award the ISO 9001: 2015, ISO 14001:2015, ISO 45001:2018  Management system certificate", False),
		("D3:P3", "Quality Assurance & Inspection Department", True),
		("D4:P4", "Executive Standard: IEC 60793-1-40", True),
		("D5:P5", "Attenuation Test Results", True)
	]

	for rng, txt, bold in titles:
		safe_merge(ws, rng)
		c = ws[rng.split(":")[0]]
		c.value = txt
		c.alignment = center
		c.font = Font(bold=bold, size=12 if "D1" in rng else 11)

	row = 6

	# --- Sales Order & Date ---
	po_no = frappe.db.get_value("Sales Order", {"name": doc.sales_order}, "po_no")
	formatted_date = ""
	if doc.report_date:
		try:
			formatted_date = datetime.strptime(str(doc.report_date), "%Y-%m-%d").strftime("%d-%m-%Y")
		except:
			formatted_date = str(doc.report_date)

	# --- Info Rows ---
	info_data = [
		("Description", doc.description),
		("Drum Tag No.", doc.custom_drum_tag_no),
		("Sales Order No.", doc.sales_order),
		("P.O No.", po_no),
		("Cable ID", doc.custom_cable_id),
		("Customer", doc.custom_customer),
		("Reference No.", doc.custom_reference_no),
		("Refractive Index"," "),
		("Optical Length (M)", doc.custom_optical_length, "Physical Length (M)", doc.custom_physical_length),
		("Date of Testing", formatted_date)
	]

	total_rows = len(info_data)
	half = total_rows // 2
	left_info = info_data[:half]
	right_info = info_data[half:]

	# --- Write left info ---
	for entry in left_info:
		if len(entry) == 4:
			opt_label, opt_value, phy_label, phy_value = entry
			ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
			ws.cell(row=row, column=1, value=opt_label).alignment = center
			ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=4)
			ws.cell(row=row, column=3, value=opt_value).alignment = left_align
			for c in range(1, 5):
				ws.cell(row=row, column=c).border = border
		else:
			label, value = entry
			ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
			ws.cell(row=row, column=1, value=label).alignment = center
			ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=8)
			ws.cell(row=row, column=3, value=value).alignment = left_align
			for c in range(1, 7):
				ws.cell(row=row, column=c).border = border
		row += 1

	# --- Write right info ---
	row_right = row - len(left_info)
	for entry in right_info:
		if len(entry) == 4:
			opt_label, opt_value, phy_label, phy_value = entry
			ws.merge_cells(start_row=row_right, start_column=9, end_row=row_right, end_column=10)
			ws.cell(row=row_right, column=9, value=opt_label).alignment = left_align
			ws.merge_cells(start_row=row_right, start_column=11, end_row=row_right, end_column=11)
			ws.cell(row=row_right, column=11, value=opt_value).alignment = left_align
			for c in range(7, 11):
				ws.cell(row_right, c).border = border
			ws.merge_cells(start_row=row_right, start_column=12, end_row=row_right, end_column=13)
			ws.cell(row=row_right, column=12, value=phy_label).alignment = left_align
			ws.merge_cells(start_row=row_right, start_column=14, end_row=row_right, end_column=16)
			ws.cell(row=row_right, column=14, value=phy_value).alignment = left_align
			for c in range(11, 17):
				ws.cell(row_right, c).border = border
		else:
			label, value = entry
			ws.merge_cells(start_row=row_right, start_column=9, end_row=row_right, end_column=11)
			ws.cell(row=row_right, column=9, value=label).alignment = left_align
			ws.merge_cells(start_row=row_right, start_column=12, end_row=row_right, end_column=16)
			ws.cell(row=row_right, column=12, value=value).alignment = left_align
			for c in range(7, 17):
				ws.cell(row_right, c).border = border
		row_right += 1
	row = max(row, row_right)
	max_1310 = min_1310 = max_1550 = min_1550 = avg_1310 = avg_1550 = 0

	
	skip_table = getattr(doc, "custom_attenuation_optional", 1)  
	if not skip_table:
		for base_col in [1, 9]:  
			ws.merge_cells(start_row=row, start_column=base_col, end_row=row, end_column=base_col+1)
			ws.cell(row=row, column=base_col, value="Loose Tube").alignment = center

			ws.merge_cells(start_row=row, start_column=base_col+2, end_row=row, end_column=base_col+3)
			ws.cell(row=row, column=base_col+2, value="Fiber").alignment = center

			ws.merge_cells(start_row=row, start_column=base_col+4, end_row=row, end_column=base_col+6)
			ws.cell(row=row, column=base_col+4, value="Attenuation (dB/Km)").alignment = center

			ws.merge_cells(start_row=row, start_column=base_col+7, end_row=row+1, end_column=base_col+7)
			ws.cell(row=row, column=base_col+7, value="Remarks").alignment = center


			for i in range(8):
				ws.cell(row=row, column=base_col+i).border = border
				ws.cell(row=row+1, column=base_col+i).border = border

			sub_headers = ["SL. No", "Colour", "No", "Colour", "1310 nm", "1550 nm","1625 nm"]
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
			7: 12,   # 1625nm
			8: 25,   # Remarks
			9: 6,    # SL. No (Right Table)
			10: 12,  # Tube Colour
			11: 6,   # No
			12: 12,  # Fiber Colour
			13: 12,  # 1310nm
			14: 12,  # 1550nm
			15: 12,  # 1625nm
			16: 25   # Remarks (Right)
		}
		for col, width in column_widths.items():
			ws.column_dimensions[get_column_letter(col)].width = width
		# --- Attenuation Data ---
		# attenuation = doc.custom_attenuation or []
		# attenuation.sort(key=lambda x: x.tube_colour)
		# groups = [list(g) for k, g in groupby(attenuation, key=lambda x: x.tube_colour)]
		# half = (len(groups)+1)//2
		# left_data = [item for g in groups[:half] for item in g]
		# right_data = [item for g in groups[half:] for item in g]
		
		# --- Attenuation Data Split ---
		attenuation = doc.custom_attenuation or []
		# Sort by tube colour
		# attenuation.sort(key=lambda x: x.tube_colour)

		# Determine fiber count
		fiber_count = len(attenuation)

		if fiber_count <= 12:
			left_data = attenuation
			right_data = []
		else:
			left_data = attenuation[:12]
			right_data = attenuation[12:]


		s_no = 1
		all_1310 = []
		all_1550 = []
		all_1625 =[]

		def write_side(data, base_col, serial_start):
			current_row = row
			serial = serial_start
			i = 0
			while i < len(data):
				color = data[i].tube_colour
				same_color_rows = [x for x in data[i:] if x.tube_colour == color]
				merge_count = len(same_color_rows)
				no_count = 1

				# Merge Tube Colour for visual grouping
				if merge_count > 1:
					ws.merge_cells(start_row=current_row, start_column=base_col+1,
								end_row=current_row+merge_count-1, end_column=base_col+1)
					ws.cell(row=current_row, column=base_col+1, value=color).alignment = center
					ws.cell(row=current_row, column=base_col+1).border = border

					# Optional: merge Remarks column if needed
					ws.merge_cells(start_row=current_row, start_column=base_col+7,
								end_row=current_row+merge_count-1, end_column=base_col+7)
					ws.cell(row=current_row, column=base_col+7, value=doc.remarks).alignment = center
					

				for j, r in enumerate(same_color_rows):
					ws.cell(row=current_row+j, column=base_col, value=serial).alignment = center
					ws.cell(row=current_row+j, column=base_col).border = border

					ws.cell(row=current_row+j, column=base_col+2, value=no_count).alignment = center
					ws.cell(row=current_row+j, column=base_col+2).border = border

					ws.cell(row=current_row+j, column=base_col+3, value=r.fiber_colour).alignment = center
					ws.cell(row=current_row+j, column=base_col+3).border = border

					# Write all attenuation values in every row (no merge)
					ws.cell(row=current_row+j, column=base_col+4, value=r.attenuation_at_1310_nm).alignment = center
					ws.cell(row=current_row+j, column=base_col+4).border = border

					ws.cell(row=current_row+j, column=base_col+5, value=r.attenuation_at_1550_nm).alignment = center
					ws.cell(row=current_row+j, column=base_col+5).border = border

					ws.cell(row=current_row+j, column=base_col+6, value=r.attenuation_at_1625_nm).alignment = center
					ws.cell(row=current_row+j, column=base_col+6).border = border
	 
					ws.cell(row=current_row+j, column=base_col+7).border = border

					serial += 1
					no_count += 1
				i += merge_count
				current_row += merge_count
			return current_row, serial


		
		left_end, next_s_no = write_side(left_data, 1, s_no)
		right_end, _ = write_side(right_data, 9, next_s_no)
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
		ws.merge_cells(start_row=customer_req_start_row-1,
					start_column=1, end_row=customer_req_start_row-1, end_column=16)
		verified_by = getattr(doc, "verified_by", "") or ""
		for col in range(1, 17):
			ws.cell(row=customer_req_start_row-1, column=col).border = border
			ws.merge_cells(start_row=customer_req_start_row,
					start_column=1, end_row=customer_req_start_row, end_column=16)
			ws.cell(row=customer_req_start_row, column=1,
					value="# This report has been generated in laboratory at room temperature.").alignment = left_align
			ws.merge_cells(start_row=customer_req_start_row+1,
					start_column=1, end_row=customer_req_start_row+4, end_column=7)
			ws.cell(row=customer_req_start_row+1, column=1,
					value="Note:- Attenuation & Continuity OK ").alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
			ws.merge_cells(start_row=customer_req_start_row+1,
					start_column=8, end_row=customer_req_start_row+9, end_column=16)
			ws.cell(row=customer_req_start_row+1, column=8,
					value=f"Verified By: {verified_by}").alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
		for r in range(customer_req_start_row+1, customer_req_start_row+10):  # end_row +1
			for c in range(8, 17):  # end_column +1
				ws.cell(row=r, column=c).border = border
		
  
		for col in range(1, 17):
			ws.cell(row=customer_req_start_row, column=col).border = border
		for row in range(customer_req_start_row+1, customer_req_start_row+5):
			for col in range(8, 17):  
				ws.cell(row=row, column=col).border = border
		row = customer_req_start_row + 5

		tested_by = getattr(doc, "inspected_by", "") or ""
		# verified_by = getattr(doc, "verified_by", "") or ""

		ws.merge_cells(start_row=row, start_column=1, end_row=row+4, end_column=7)
		for r in range(row, row + 5):  
			for c in range(1, 8):     
				ws.cell(row=r, column=c).border = border
		ws.cell(row=row, column=1, value=f"Tested By: {tested_by}").alignment = left_align
		# border_1 = Border(left=thin, right=thin,  bottom=thin)
		# ws.merge_cells(start_row=row, start_column=8, end_row=row+4, end_column=16)
		# for r in range(row, row + 5): 
		# 	for c in range(8,17):     
		# 		ws.cell(row=r, column=c).border = border_1
		# ws.cell(row=row, column=8, value=f"Verified By: {verified_by}").alignment = left_align

		for c in range(1, 17):
			ws.cell(row, c).border = border

		row += 5

		# === Address & Website ===
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

		ws.merge_cells(start_row=row, start_column=1, end_row=row+1, end_column=16)
		ws.cell(row=row, column=1, value="Plot No.176 , Block 21 , Mina Abdulla Industrial Area , Al Ahamadi Governorate , Kuwait\nWebsite: www.taihankuwait.com").alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
		for r in range(row, row+2):  
			for c in range(1, 17):  
				ws.cell(row=r, column=c).border = thin_border

		row += 2


	else:
		row = 11
		# Customer Req. top row
		customer_req_start_row = row
		ws.merge_cells(start_row=customer_req_start_row, start_column=1, end_row=customer_req_start_row, end_column=16)
		for row in ws.iter_rows(min_row=customer_req_start_row,
                        max_row=customer_req_start_row,
                        min_col=1,
                        max_col=16):
			for cell in row:
				cell.border = border
		ws.cell(
			row=customer_req_start_row,
			column=1,
			value="# This report has been generated in laboratory at room temperature."
		).alignment = left_align

		ws.merge_cells(start_row=customer_req_start_row+1, start_column=1, end_row=customer_req_start_row+5, end_column=7)
		ws.cell(
			row=customer_req_start_row+1,
			column=1,
			value="Note:- Attenuation & Continuity OK "
		).alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
		for row in ws.iter_rows(min_row=customer_req_start_row+1,
                        max_row=customer_req_start_row+5,
                        min_col=1,
                        max_col=7):
			for cell in row:
				cell.border = border


		for r in range(customer_req_start_row, customer_req_start_row):
			for c in range(1, 17):
				ws.cell(r, c).border = border


		if doc.custom_single_attenuation:
			table_row = customer_req_start_row + 1

			ws.merge_cells(start_row=table_row, start_column=8, end_row=table_row+1, end_column=10)
			ws.cell(row=table_row, column=8, value="Customer Req.").alignment = center
			ws.merge_cells(start_row=table_row+1, start_column=11, end_row=table_row+1, end_column=12)
			ws.cell(row=table_row+1, column=11, value=" ").alignment = center
			ws.merge_cells(start_row=table_row+1, start_column=13, end_row=table_row+1, end_column=14)
			ws.cell(row=table_row+1, column=13, value= " ").alignment = center
			ws.merge_cells(start_row=table_row+1, start_column=15, end_row=table_row+1, end_column=16)
			ws.cell(row=table_row+1, column=15, value= " ").alignment = center
			for row in ws.iter_rows(min_row=table_row+1,
                        max_row=table_row+1,
                        min_col=11,
                        max_col=12):
				for cell in row:
					cell.border = border
			for row in ws.iter_rows(min_row=table_row+1,
                        max_row=table_row+1,
                        min_col=13,
                        max_col=14):
				for cell in row:
					cell.border = border
			for row in ws.iter_rows(min_row=table_row+1,
                        max_row=table_row+1,
                        min_col=15,
                        max_col=16):
				for cell in row:
					cell.border = border

			ws.merge_cells(start_row=table_row, start_column=11, end_row=table_row, end_column=12)
			ws.cell(row=table_row, column=11, value="1310 nm").alignment = center

			ws.merge_cells(start_row=table_row, start_column=13, end_row=table_row, end_column=14)
			ws.cell(row=table_row, column=13, value="1550 nm").alignment = center

			ws.merge_cells(start_row=table_row, start_column=15, end_row=table_row, end_column=16)
			ws.cell(row=table_row, column=15, value="1625 nm").alignment = center

			for col in range(8, 16):
				ws.cell(row=table_row, column=col).border = border
				ws.cell(row=table_row, column=col).fill = blue_fill
				ws.cell(row=table_row+1, column=col).fill = blue_fill

			row = table_row + 2
			for child in doc.custom_single_attenuation:
				ws.merge_cells(start_row=row, start_column=8, end_row=row, end_column=10)
				ws.cell(row=row, column=8, value=child.type).alignment = center  
				ws.merge_cells(start_row=row, start_column=11, end_row=row, end_column=12)
				ws.cell(row=row, column=11, value=child.get("1310_nm") or "").alignment = center

				ws.merge_cells(start_row=row, start_column=13, end_row=row, end_column=14)
				ws.cell(row=row, column=13, value=child.get("1550_nm") or "").alignment = center

				ws.merge_cells(start_row=row, start_column=15, end_row=row, end_column=16)
				ws.cell(row=row, column=15, value=child.get("1625_nm") or "").alignment = center


				for c in range(8, 17):
					ws.cell(row=row, column=c).border = border

				row += 1




		ws.merge_cells(start_row=row, start_column=1, end_row=row+3, end_column=7)
		for r in ws.iter_rows(min_row=row, max_row=row+3, min_col=1, max_col=7):
			for cell in r:
				cell.border = border
		ws.cell(row=row, column=1, value=f"Tested By: {getattr(doc, 'inspected_by', '')}").alignment = left_align

		ws.merge_cells(start_row=row, start_column=8, end_row=row+3, end_column=16)
		for r in ws.iter_rows(min_row=row, max_row=row+3, min_col=8, max_col=16):
			for cell in r:
				cell.border = border
		verified_by = getattr(doc, 'verified_by', '')  
		value_text = f"Verified By: {verified_by} " if verified_by else "Verified By: "

		ws.cell(row=row, column=8, value=value_text).alignment = left_align



		for c in range(1, 17):
			ws.cell(row=row, column=c).border = border

		# --- Address & Website ---
		row += 4
		ws.merge_cells(start_row=row, start_column=1, end_row=row+1, end_column=16)
		ws.cell(
			row=row, column=1,
			value="Plot No.176 , Block 21 , Mina Abdulla Industrial Area , Al Ahamadi Governorate , Kuwait\nWebsite: www.taihankuwait.com"
		).alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

		for r in range(row, row+2):
			for c in range(1, 17):
				ws.cell(r, c).border = border
	
	column_widths = {
			1: 6,    # SL. No
			2: 12,   # Tube Colour
			3: 6,    # No
			4: 12,   # Fiber Colour
			5: 12,   # 1310nm
			6: 12,   # 1550nm
			7: 12,   # 1625nm
			8: 25,   # Remarks
			9: 6,    # SL. No (Right Table)
			10: 12,  # Tube Colour
			11: 6,   # No
			12: 12,  # Fiber Colour
			13: 12,  # 1310nm
			14: 12,  # 1550nm
			15: 12,  # 1625nm
		}
	for col, width in column_widths.items():
		ws.column_dimensions[get_column_letter(col)].width = width



	# --- Save Excel ---
	output = io.BytesIO()
	wb.save(output)
	output.seek(0)
	frappe.response["filename"] = "Buffering Single Mode Final.xlsx"
	frappe.response["filecontent"] = output.getvalue()
	frappe.response["type"] = "binary"


def safe_merge(ws, cell_range):
	if cell_range in ws.merged_cells:
		ws.unmerge_cells(cell_range)
	ws.merge_cells(cell_range)


