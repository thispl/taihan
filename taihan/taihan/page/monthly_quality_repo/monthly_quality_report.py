# import frappe
# from frappe.utils import flt, today, get_first_day
# from collections import defaultdict
# import calendar

# @frappe.whitelist()
# def get_monthly_quality_data(from_date=None, to_date=None):
#     if not from_date or not to_date:
#         from_date = get_first_day(today())
#         to_date = today()

#     work_orders = frappe.get_all("Work Order",
#         filters={
#             "custom_testing_date": ["between", [from_date, to_date]],
#             "docstatus":("!=",2)
#         },
#         fields=["name", "custom_otdr_lengthm", "custom_hold_length_m","custom_observation__km"]
#     )

#     if not work_orders:
#         return {"fpy_table": [], "monthly_ckm": 0}

#     wo_map = {
#         wo.name: {
#             "otdr_length": flt(wo.custom_otdr_lengthm),
#             "hold_length": flt(wo.custom_hold_length_m),
#             "observation": flt(wo.custom_observation__km)
#         }
#         for wo in work_orders
#     }
#     wo_names = list(wo_map.keys())

#     operations = frappe.get_all("Work Order Operation",
#         filters={"parent": ["in", wo_names]},
#         fields=["parent", "operation"]
#     )

#     operation_summary = defaultdict(lambda: {"total_output": 0, "hold": 0,"observation": 0})
#     total_ckm = 0

#     for op in operations:
#         wo_data = wo_map.get(op.parent)
#         if not wo_data:
#             continue

#         operation_name = op.operation
#         otdr_km = wo_data["otdr_length"]
#         hold_km = wo_data["hold_length"]
#         obs_km = wo_data["observation"]
#         operation_summary[operation_name]["total_output"] += otdr_km
#         operation_summary[operation_name]["hold"] += hold_km
#         operation_summary[operation_name]["observation"] += obs_km
#         total_ckm += otdr_km

#     fpy_table = []
#     for operation, data in operation_summary.items():
#         total_output = data["total_output"]
#         hold = data["hold"]
#         observation=data["observation"]
#         released_ok = total_output - hold
#         pass_rate = (released_ok / total_output) * 100 if total_output else 0

#         fpy_table.append({
#             "operation": operation,
#             "total_output": round(total_output, 2),
#             "observation": round(observation,2),  # Leave blank if not needed
#             "hold": round(hold, 2),
#             "released_ok": round(released_ok, 2),
#             "pass_rate": round(pass_rate, 2)
#         })

#     return {
#         "fpy_table": fpy_table,
#     }


# import calendar
# from frappe.utils import getdate, add_months, today
# import frappe

# @frappe.whitelist()
# def get_output_ckm_by_month(from_date=None, to_date=None):
#     if not from_date or not to_date:
#         current_date = getdate(today())
#         from_date = getdate(f"{current_date.year - 1}-12-01")
#         to_date = current_date
#     else:
#         from_date = getdate(from_date)
#         to_date = getdate(to_date)

#     months_list = []
#     current = getdate(f"{from_date.year}-{from_date.month:02d}-01")

#     while current <= to_date:
#         yyyy = current.year
#         mm = current.month
#         label = f"{calendar.month_abbr[mm]}-{str(yyyy)[-2:]}"
#         months_list.append((label, f"{mm:02d}", str(yyyy)))
#         current = add_months(current, 1)

#     result = []
#     total_output = 0

#     for label, mm, yyyy in months_list:
#         month_start = f"{yyyy}-{mm}-01"
#         last_day = calendar.monthrange(int(yyyy), int(mm))[1]
#         month_end = f"{yyyy}-{mm}-{last_day}"

#         if getdate(month_end) < from_date or getdate(month_start) > to_date:
#             continue

#         month_output = frappe.db.sql("""
#             SELECT SUM(CAST(custom_otdr_lengthm AS DECIMAL(10,2)))
#             FROM `tabWork Order`
#             WHERE custom_testing_date BETWEEN %s AND %s AND docstatus!=2
#         """, (month_start, month_end))[0][0] or 0

#         total_output += month_output

#         result.append({
#             "label": label,
#             "value": round(month_output, 2)
#         })

#     avg_ckm = round(total_output / len(result), 2) if result else 0

#     return {
#         "history": result,
#         "average_ckm": avg_ckm
#     }

import frappe
from frappe.utils import flt, today, get_first_day
from collections import defaultdict

@frappe.whitelist()
def get_monthly_quality_data(from_date=None, to_date=None):
    if not from_date or not to_date:
        from_date = get_first_day(today())
        to_date = today()

    reports = frappe.get_all(
        "Inprocess Testing Report",
        filters={
            "testing_date": ["between", [from_date, to_date]],
        },
        fields=[
            "name", "operation_name",
            "sheathing_otdr_length", "hold_sheathing", "observation_sheathing",
            "sec_otdr_length", "hold_length_m", "observation__km",
            "strand_otdr_length", "stranding_hold", "stranding_observation"
        ]
    )

    if not reports:
        return {"fpy_table": []}

    # Summary by operation
    operation_summary = defaultdict(lambda: {"total_output": 0, "hold": 0, "observation": 0})

    for r in reports:
        operation = r.operation_name

        if operation == "Buffering":
            otdr_km = flt(r.sec_otdr_length)
            hold_km = flt(r.hold_length_m)
            obs_km = flt(r.observation__km)
        elif operation == "Stranding":
            otdr_km = flt(r.strand_otdr_length)
            hold_km = flt(r.stranding_hold)
            obs_km = flt(r.stranding_observation)
        elif operation == "Jacketing":
            otdr_km = flt(r.sheathing_otdr_length)
            hold_km = flt(r.hold_sheathing)
            obs_km = flt(r.observation_sheathing)
        else:
            # Unknown operation: skip
            continue

        operation_summary[operation]["total_output"] += otdr_km
        operation_summary[operation]["hold"] += hold_km
        operation_summary[operation]["observation"] += obs_km

    # Prepare FPY table
    fpy_table = []
    for operation, data in operation_summary.items():
        total_output = data["total_output"]
        hold = data["hold"]
        observation = data["observation"]
        released_ok = total_output - hold
        pass_rate = (released_ok / total_output) * 100 if total_output else 0

        fpy_table.append({
            "operation": operation,
            "total_output": round(total_output, 2),
            "observation": round(observation, 2),
            "hold": round(hold, 2),
            "released_ok": round(released_ok, 2),
            "pass_rate": round(pass_rate, 2)
        })

    return {"fpy_table": fpy_table}


import calendar
from frappe.utils import getdate, add_months, today, flt
import frappe

@frappe.whitelist()
def get_output_ckm_by_month(from_date=None, to_date=None):
    if not from_date or not to_date:
        current_date = getdate(today())
        from_date = getdate(f"{current_date.year - 1}-12-01")
        to_date = current_date
    else:
        from_date = getdate(from_date)
        to_date = getdate(to_date)

    months_list = []
    current = getdate(f"{from_date.year}-{from_date.month:02d}-01")

    while current <= to_date:
        yyyy = current.year
        mm = current.month
        label = f"{calendar.month_abbr[mm]}-{str(yyyy)[-2:]}"
        months_list.append((label, f"{mm:02d}", str(yyyy)))
        current = add_months(current, 1)

    result = []
    total_output = 0

    for label, mm, yyyy in months_list:
        month_start = f"{yyyy}-{mm}-01"
        last_day = calendar.monthrange(int(yyyy), int(mm))[1]
        month_end = f"{yyyy}-{mm}-{last_day}"

        if getdate(month_end) < from_date or getdate(month_start) > to_date:
            continue

        # Fetch data for the month
        reports = frappe.get_all(
            "Inprocess Testing Report",
            filters={
                "testing_date": ["between", [month_start, month_end]],
                "docstatus": ["!=", 2]
            },
            fields=[
                "operation_name",
                "sec_otdr_length", "strand_otdr_length", "sheathing_otdr_length"
            ]
        )

        month_output = 0
        for r in reports:
            if r.operation_name == "Buffering":
                month_output += flt(r.sec_otdr_length)
            elif r.operation_name == "Stranding":
                month_output += flt(r.strand_otdr_length)
            elif r.operation_name == "Jacketing":
                month_output += flt(r.sheathing_otdr_length)

        total_output += month_output

        result.append({
            "label": label,
            "value": round(month_output, 2)
        })

    avg_ckm = round(total_output / len(result), 2) if result else 0

    return {
        "history": result,
        "average_ckm": avg_ckm
    }
