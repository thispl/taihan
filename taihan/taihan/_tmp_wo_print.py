import frappe, re, json


def render_wo(name="MFG-WO-2026-00213"):
    html = frappe.get_print("Work Order", name, "Work Order Production Paper", no_letterhead=1, as_pdf=False)
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    checks = ["WORK ORDER", "PRODUCTION ORDER", name, "Jacketing", "AHAK INTERNATIONAL",
              "Customer Number", "Customer Name", "Sales Order Number", "Loose Tube Colours", "Total Planned Quantity",
              "JOB CARDS CREATED AGAINST THIS WORK ORDER", "PO-JOB00674"]
    with open("/tmp/wo_print.html", "w") as f:
        f.write(html)
    return {c: (c in text) for c in checks}
