app_name = "taihan"
app_title = "Taihan"
app_publisher = "Teampro"
app_description = "Taihan"
app_email = "erp@groupteampro.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "taihan",
# 		"logo": "/assets/taihan/logo.png",
# 		"title": "Taihan",
# 		"route": "/taihan",
# 		"has_permission": "taihan.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/taihan/css/taihan.css"
# app_include_js = "/assets/taihan/js/taihan.js"

# include js, css files in header of web template
# web_include_css = "/assets/taihan/css/taihan.css"
# web_include_js = "/assets/taihan/js/taihan.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "taihan/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"Job Card": "public/js/job_card_partial.js",
	"Production Plan": "public/js/production_plan.js",
	"Work Order": "public/js/work_order.js",
        "Stock Entry": "public/js/stock_entry.js",
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "taihan/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environmentS
jinja = {
    "methods": [
		"taihan.taihan.job_card.job_card_print",
		"taihan.taihan.job_card.work_order_print",
		"taihan.taihan.job_card.get_batch_values",
		"taihan.taihan.job_card.get_final_batch",
		"taihan.taihan.job_card.get_barcode_svg",
		"taihan.taihan.job_card.get_barcode_img",
		"taihan.taihan.job_card.get_job_cards_for_work_order",
	]
	# "methods": "taihan.utils.jinja_methods",
# 	"filters": "taihan.utils.jinja_filters"
}

# Installation
# ------------

# before_install = "taihan.install.before_install"
# after_install = "taihan.install.after_install"
after_migrate = "taihan.taihan.job_card.ensure_overproduction_approval_fields"

# Uninstallation
# ------------

# before_uninstall = "taihan.uninstall.before_uninstall"
# after_uninstall = "taihan.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "taihan.utils.before_app_install"
# after_app_install = "taihan.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "taihan.utils.before_app_uninstall"
# after_app_uninstall = "taihan.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "taihan.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Production Plan": "taihan.taihan.production_plan.CustomProductionPlan",
}

# Document Events
# ---------------
# Hook on document methods and events


doc_events = {
    "Stock Entry": {
        "before_validate": "taihan.taihan.stock_entry.sync_stock_entry_batch_numbers",
        "on_submit": "taihan.taihan.stock_entry.sync_submitted_stock_entry_batches"
    },
	"Journal Entry": {
		# "on_update": "method",
		# "on_cancel": "method",
		# "on_trash": "method"
        "on_submit":["taihan.taihan.journal_entry.update_expenses"],
        "on_cancel":["taihan.taihan.journal_entry.update_expenses_cancel"]
	},
	"Leave Application": {
		"validate": ["taihan.taihan.leave_application.validate_leave_application","taihan.taihan.leave_application.validate_hajj_leave","taihan.taihan.leave_application.validate_umrah_leave_la"],
	},
	"Quotation":{
		"validate": ["taihan.taihan.quotation.quotation_notification"],
		"before_submit": "taihan.taihan.quotation.quotation_notification_before_submit",
		"before_insert":"taihan.utils.autoname_quotation",
		"after_insert":"taihan.utils.update_quotation_series",
		# "before_save":"taihan.custom.update_naming_series_quotation"
	},
	"Material Request":{
     "on_submit":"taihan.taihan.material_request.send_alert_mail_rol",
    #  "validate":"taihan.custom.send_alert_mail_rol"
    },
	"Cost Estimation":{
		"validate":"taihan.taihan.cost_estimation.update_values_cost_estimation"
     },
 	"Request for Quotation":{
     "on_submit":"taihan.taihan.request_for_quotation.send_rfq_pdf"
    },
	"Quality Inspection":{
		"after_insert":"taihan.taihan.quality_inspection.update_barcode",
		"on_submit":"taihan.taihan.doctype.inprocess_testing_report.inprocess_testing_report.create_inprocess_report"
	},
	"Work Order":{
		"before_insert": "taihan.taihan.work_order.before_insert_work_order",
		"validate": "taihan.taihan.work_order.validate_work_order",
		"on_trash": "taihan.taihan.job_card.delete_testing_report",
	},
	"Production Plan":{
		"validate": "taihan.taihan.production_plan.validate_production_plan",
		"before_save": "taihan.taihan.production_plan.update_warehouse_sub_assembly_item"
	},
	# "BOM":{
	# 	"on_submit":"taihan.custom.update_valuation_rate",
	# },
	"Job Card":{
		"after_insert":"taihan.taihan.job_card.update_tube_color",
		"before_save": "taihan.taihan.job_card.before_save_job_card",
  		"on_submit":["taihan.taihan.job_card.create_stock_entry","taihan.taihan.job_card.create_quality_inspection","taihan.taihan.job_card_partial.update_operation_completed_qty","taihan.taihan.job_card.sync_submitted_job_card_status"],
        "before_submit": "taihan.taihan.job_card.validate_excess_material_transfer"
		# "on_update_after_submit":"taihan.custom.delete_stock_entry",
	},
	# "Downtime Entry":{
	# 	"before_insert":"taihan.custom.update_memo_no",
	# }
    "Delivery Note":{
        "before_submit":"taihan.taihan.delivery_note.set_inspected_by"
	},
    "Batch":{
        "before_naming": "taihan.utils.autoname_batch"
	}
	

}

# override_doctype_class = {
#     "Leave Application":"taihan.overrides.CustomLeaveApplication"
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"taihan.tasks.all"
# 	],
# 	"daily": [
# 		"taihan.tasks.daily"
# 	],
# 	"hourly": [
# 		"taihan.tasks.hourly"
# 	],
# 	"weekly": [
# 		"taihan.tasks.weekly"
# 	],
# 	"monthly": [
# 		"taihan.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "taihan.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
    "erpnext.stock.utils.get_incoming_rate": "taihan.taihan.stock_entry.get_incoming_rate",
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "taihan.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["taihan.utils.before_request"]
# after_request = ["taihan.utils.after_request"]

# Job Events
# ----------
# before_job = ["taihan.utils.before_job"]
# after_job = ["taihan.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"taihan.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

