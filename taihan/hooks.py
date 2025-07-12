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
# doctype_js = {"doctype" : "public/js/doctype.js"}
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
		"taihan.custom.job_card_print",
		"taihan.custom.work_order_print",
		"taihan.custom.get_batch_values",
		"taihan.custom.get_final_batch",
	]
	# "methods": "taihan.utils.jinja_methods",
# 	"filters": "taihan.utils.jinja_filters"
}

# Installation
# ------------

# before_install = "taihan.install.before_install"
# after_install = "taihan.install.after_install"

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

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events


doc_events = {
	"Journal Entry": {
		# "on_update": "method",
		# "on_cancel": "method",
		# "on_trash": "method"
        "on_submit":["taihan.custom.update_expenses"],
        "on_cancel":["taihan.custom.update_expenses_cancel"]
	},
	"Leave Application": {
		"validate": ["taihan.custom.validate_leave_application","taihan.custom.validate_hajj_leave","taihan.custom.validate_umrah_leave_la"],
	},
	"Quotation":{
		"validate": "taihan.custom.quotation_notification",
		"before_submit": "taihan.custom.quotation_notification_before_submit",
		"before_save":"taihan.custom.update_naming_series_quotation"
	},
	"Material Request":{
     "on_submit":"taihan.custom.send_alert_mail_rol",
    #  "validate":"taihan.custom.send_alert_mail_rol"
    },
	"Cost Estimation":{
		"validate":"taihan.custom.update_values_cost_estimation"
     },
 	"Request for Quotation":{
     "on_submit":"taihan.custom.send_rfq_pdf"
    },
	"Quality Inspection":{
		"after_insert":"taihan.custom.update_barcode"
	},
	
	

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
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "taihan.event.get_events"
# }
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

