import frappe
from frappe.model.document import Document


@frappe.whitelist()
def set_cost_details():
    details = frappe.db.get_all("Cost Estimation Details", fields=["title"], order_by="creation asc")
    return [d.title for d in details]


from datetime import datetime
@frappe.whitelist()
def update_values_cost_estimation(doc,method):
    if doc.cost_estimation_items:
        for i in doc.cost_estimation_items:
            if i.cost_estimation_details=="Salary ( Total Working Days )":
                i.number_value_percentage=doc.total_working_days
                non_production_emp=frappe.db.sql(""" select sum(ctc) as total from `tabEmployee` where custom_employee_type="Non Production" and status="Active" """,as_dict=True)
                i.total = non_production_emp[0].total or 0
                if i.total:
                    i.value_used=(doc.total_working_days* i.total)/26
            if i.cost_estimation_details=="Salary - Admin cost":
                i.number_value_percentage=doc.total_working_days
                non_production_emp=frappe.db.sql(""" select sum(ctc) as total from `tabEmployee` where custom_employee_type="Production" and status = "Active" """,as_dict=True)
                i.total = non_production_emp[0].total or 0
                if i.total:
                    i.value_used=(doc.total_working_days* i.total)/26
            if i.cost_estimation_details=="Car Admin cost":
                value=frappe.db.get_value("Cost of sales Fixed Details",{"statement":"Car Admin cost"},["fixed_value"])
                i.number_value_percentage=value
                i.value_used=(value/26)*doc.total_working_days
                i.total =i.value_used
            if i.cost_estimation_details=="House Admin cost":
                value=frappe.db.get_value("Cost of sales Fixed Details",{"statement":"House Admin cost"},["fixed_value"])
                i.number_value_percentage=value
                i.value_used=(value/26)*doc.total_working_days
                i.total =i.value_used
            if i.cost_estimation_details=="Factory rent":
                value=frappe.db.get_value("Cost of sales Fixed Details",{"statement":"Factory rent"},["fixed_value"])
                i.number_value_percentage=doc.total_working_days
                i.total=value
                if i.total:
                    i.value_used=(i.total/26)*doc.total_working_days
                
            if i.cost_estimation_details=="WATER":
                value=frappe.db.get_value("Cost of sales Fixed Details",{"statement":"WATER"},["fixed_value"])
                i.number_value_percentage=value
                i.total=value
                i.value_used=value
            if i.cost_estimation_details=="Electrical power":
                value=frappe.db.get_value("Cost of sales Fixed Details",{"statement":"Electrical power"},["fixed_value"])
                i.number_value_percentage=doc.total_working_days
                i.total=doc.total_working_days
                i.value_used=value
            if i.cost_estimation_details=="Depreciation":
                i.number_value_percentage=doc.total_working_days
                posting_date = datetime.strptime(doc.posting_date, "%Y-%m-%d")
                month = posting_date.month
                year = posting_date.year

                depreciation_sum = frappe.db.sql("""
                    SELECT SUM(ds.depreciation_amount) AS total
                    FROM `tabAsset Depreciation Schedule` ads
                    JOIN `tabDepreciation Schedule` ds ON ds.parent = ads.name
                    WHERE MONTH(ds.schedule_date) = %s
                      AND YEAR(ds.schedule_date) = %s
                """, (month, year), as_dict=True)

                i.value_used = depreciation_sum[0].total or 0
            if i.cost_estimation_details=="Raw Material-1":
                value=frappe.db.get_value("Cost of sales Fixed Details",{"statement":"Raw Material-1"},["fixed_value"])
                i.total=value
                if i.number_value_percentage:
                    i.value_used=(value*i.number_value_percentage/100)
            if i.cost_estimation_details=="Wooden drums  ( Unit cost  37. KD )":
                value=frappe.db.get_value("Cost of sales Fixed Details",{"statement":"Wooden drums  ( Unit cost  37. KD )"},["fixed_value"])
                i.total=value
                if i.number_value_percentage:
                    i.value_used=(value*i.number_value_percentage)