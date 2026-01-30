app_name = "custom_clearance"
app_title = "Custom Clearance"
app_publisher = "Friends ERP"
app_description = "A Custom Clearance App For Ethiopian."
app_email = "friendserpnext@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "custom_clearance",
# 		"logo": "/assets/custom_clearance/logo.png",
# 		"title": "Custom Clearance",
# 		"route": "/custom_clearance",
# 		"has_permission": "custom_clearance.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/custom_clearance/css/custom_clearance.css"
# app_include_js = "/assets/custom_clearance/js/custom_clearance.js"

# include js, css files in header of web template
# web_include_css = "/assets/custom_clearance/css/custom_clearance.css"
# web_include_js = "/assets/custom_clearance/js/custom_clearance.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "custom_clearance/public/scss/website"

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
# app_include_icons = "custom_clearance/public/icons.svg"

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

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "custom_clearance.utils.jinja_methods",
# 	"filters": "custom_clearance.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "custom_clearance.install.before_install"
# after_install = "custom_clearance.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "custom_clearance.uninstall.before_uninstall"
# after_uninstall = "custom_clearance.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "custom_clearance.utils.before_app_install"
# after_app_install = "custom_clearance.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "custom_clearance.utils.before_app_uninstall"
# after_app_uninstall = "custom_clearance.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "custom_clearance.notifications.get_notification_config"

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

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"custom_clearance.tasks.all"
# 	],
# 	"daily": [
# 		"custom_clearance.tasks.daily"
# 	],
# 	"hourly": [
# 		"custom_clearance.tasks.hourly"
# 	],
# 	"weekly": [
# 		"custom_clearance.tasks.weekly"
# 	],
# 	"monthly": [
# 		"custom_clearance.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "custom_clearance.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "custom_clearance.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "custom_clearance.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "custom_clearance.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["custom_clearance.utils.before_request"]
# after_request = ["custom_clearance.utils.after_request"]

# Job Events
# ----------
# before_job = ["custom_clearance.utils.before_job"]
# after_job = ["custom_clearance.utils.after_job"]

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
# 	"custom_clearance.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

