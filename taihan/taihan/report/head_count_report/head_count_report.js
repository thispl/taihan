// Copyright (c) 2025, Teampro and contributors
// For license information, please see license.txt

frappe.query_reports["Head Count Report"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default":frappe.datetime.get_today(),
			"reqd": 1
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default":frappe.datetime.get_today(),
			"reqd": 1
		},
	]
};
