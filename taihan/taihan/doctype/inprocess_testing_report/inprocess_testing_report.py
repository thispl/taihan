# Copyright (c) 2025, Teampro and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class InprocessTestingReport(Document):
	pass

@frappe.whitelist()
def create_inprocess_report(doc,method):
    if doc.quality_inspection_template:
        operation = frappe.db.get_value("Operation",{"quality_inspection_template":doc.quality_inspection_template},"name")
        report=frappe.new_doc("Inprocess Testing Report")
        report.work_order= frappe.db.get_value("Job Card",{"name":doc.reference_name},"work_order")
        report.operation_name=operation
        report.item_to_manufacture=doc.item_code
        report.item_name=doc.item_name
        report.bom_no=frappe.db.get_value("Job Card",{"name":doc.reference_name},"bom_no")
        report.manufacturing_date=frappe.db.get_value("Job Card",{"name":doc.reference_name},"posting_date")
        report.production_id=doc.custom_production_id
        report.production_od=doc.custom_production_od
        report.type_of_mode=doc.custom_type_of_mode
        report.testing_date=doc.report_date
        report.color1nm_actual=doc.custom_ior__1310_nm
        report.color1550nm_actual=doc.custom_ior__1550_nm
        report.color1625nm_actual=doc.custom_ior__1625_nm
        report.color_850nm_actual=doc.custom_ior__850_nm
        report.color_1300nm_actual=doc.custom_ior__1300_nm
        report.testing_operator=doc.inspected_by
        report.otdr_length__km=doc.custom_otdr_lengthm
        report.sales_order=doc.sales_order
        report.customer = frappe.db.get_value("Sales Order",{"name":doc.sales_order},"customer")
        report.kink_test = doc.custom_kink_test
        report.shift=doc.custom_shift
        if operation =="Buffering":
            report.fiber_count=doc.custom_fiber_count
            report.loose_tube_id=doc.custom_lt_id
            report.sec_bobbin_no=doc.custom_bobbin_no
            report.otdr_no=doc.custom_otdr_no
            report.hold_length_m=doc.custom_hold_length_m
            report.sec_otdr_length=doc.custom_otdr_lengthm
            report.sec_tube_od_min=doc.custom_lt_od_min
            report.sec_tube_id_mm=doc.custom_id_mm
            report.observation__km=doc.custom_observation_km
            report.sec_tube_thick_max=doc.custom_thickness_max
            report.sec_testing_operator=doc.inspected_by
            report.sec_tube_od_max=doc.custom_lt_od_max
            report.sec_tube_thick_min=doc.custom_thickness_min
            report.sec_shift=doc.custom_shift
            report.colour_or_description=doc.custom_lt_colour
            report.kink_test=doc.custom_kink_test
            report.sec_fiber_type= doc.custom_fiber_type

        elif operation =="Stranding":
            report.stranding_fiber_count=doc.custom_fiber_count
            report.drum_no=doc.custom_drum_no
            report.stranding_otdr=doc.custom_otdr_no
            report.strand_otdr_length=doc.custom_otdr_lengthm
            report.stranding_hold=doc.custom_hold_length_m
            report.stranding_observation=doc.custom_observation_km
            report.core_od_mm=doc.custom_core_odmm
            report.frp_od_mm=doc.custom_frp_od
            report.strand_testing_operator=doc.inspected_by
            report.starnd_shift=doc.custom_shift
            report.strand_pod_length = doc.custom_production_length
        elif operation=="Jacketing":
            report.sheathing_fiber_count=doc.custom_fiber_count
            report.observation_sheathing=doc.custom_observation_km
            report.sheathing_otdr=doc.custom_otdr_no
            report.hold_sheathing=doc.custom_hold_length_m
            report.sheathing_otdr_length=doc.custom_otdr_lengthm
            report.sheathing_drumn_no=doc.custom_drum_no
            report.sheathing_id=doc.custom_sheathing_id
            report.outer_end_top=doc.custom_top_marking
            report.inner_end_bottom=doc.custom_bottom_marking
            report.cable_type=doc.custom_cable_type
            report.sheathing_shift=doc.custom_shift
            report.sheathing_testing_operator=doc.inspected_by
            report.sheathing_fiber_type = doc.custom_fiber_type
            report.sheathing_prod_length = doc.custom_production_length
            report.sheathing_cable_thick_min= doc.custom_cable_thickness_min
            report.sheathing_cable_thick_max = doc.custom_cable_thickness_max
            report.sheathing_cable_od_min = doc.custom_cable_outer_od
            report.sheathing_cable_od_max = doc.custom_cable_outer_od_max
        report.save()
        frappe.db.commit
