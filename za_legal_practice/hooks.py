app_name = "za_legal_practice"
app_title = "ZA Legal Practice"
app_publisher = "BuFf0k"
app_description = "A full Legal Practice Solution built on Frappe and ERPNext"
app_email = "buff0k@gmail.com"
app_license = "mit"
required_apps = ["frappe/erpnext"]

# Each item in the list will be shown as an app in the apps page
add_to_apps_screen = [
	{
		"name": "za_legal_practice",
		"logo": "/assets/za_legal_practice/images/za_legal_practice_logo.png",
		"title": "ZA Legal Practice",
		"route": "desk/company",
		"has_permission": "za_legal_practice.api.has_app_permission.has_app_permission"
	}
]

fixtures = [
	{"dt": "Role", "filters": [["name", "in", [
        "Attorney",
        "Candidate Attorney",
        "Client Portal User",
        "Compliance Officer",
		"Legal Practice Administrator",
        "Managing Partner",
        "Paralegal Secretary",
        "Partner",
        "Trust Accounts Manager"
	]]]},
	{"dt": "Custom DocPerm", "filters": [["role", "in", [
        "Attorney",
        "Candidate Attorney",
		"Client Portal User",
        "Compliance Officer",
        "Legal Practice Administrator",
        "Managing Partner",
        "Paralegal Secretary",
        "Partner",
        "Trust Accounts Manager"
	]]]},
    {"dt": "Custom Field", "filters": [["name", "in",[
        "Bank Account-za_lp_legal_trust_account_section",
        "Bank Account-za_lp_is_legal_trust_account",
        "Bank Account-za_lp_trust_account_type",
        "Bank Account-za_lp_trust_account_active",
        "Bank Account-za_lp_trust_controls_column_break",
        "Bank Account-za_lp_requires_dual_approval",
        "Bank Account-za_lp_require_matter_dimension",
        "Bank Account-za_lp_block_manual_posting",
        "Bank Account-za_lp_trust_accounting_accounts_section",
        "Bank Account-za_lp_trust_creditor_account",
        "Bank Account-za_lp_trust_investment_account",
        "Bank Account-za_lp_lpff_interest_account",
        "Bank Account-za_lp_trust_accounts_column_break",
        "Bank Account-za_lp_trust_bank_charges_account",
        "Bank Account-za_lp_trust_rounding_difference_account",
        "Bank Account-za_lp_trust_account_ownership_section",
        "Bank Account-za_lp_responsible_attorney",
        "Bank Account-za_lp_practice_branch",
        "Bank Account-za_lp_practice_area",
        "Bank Account-za_lp_trust_notes_column_break",
        "Bank Account-za_lp_trust_account_notes"
    ]]]},
    {"dt": "Matter Stage", "filters": [["name", "in", [
        "ENQUIRY",
        "CONFLICT_CHECK",
        "FICA_MANDATE",
        "MATTER_OPENING",
        "INITIAL_CONSULTATION",
        "INVESTIGATION",
        "DRAFTING",
        "FILING_LODGEMENT",
        "NEGOTIATION",
        "HEARING_APPEARANCE",
        "SETTLEMENT_FINALISATION",
        "BILLING_TRUST_FINALISATION",
        "CLOSED"
    ]]]},
    {"dt": "Legal Party Role", "filters": [["name", "in", [
        "CLIENT",
        "PLAINTIFF",
        "DEFENDANT",
        "APPLICANT",
        "RESPONDENT",
        "PURCHASER",
        "SELLER",
        "TRANSFEROR",
        "TRANSFEREE",
        "DEBTOR",
        "CREDITOR",
        "SURETY",
        "WITNESS",
        "EXPERT_WITNESS",
        "OPPOSING_ATTORNEY",
        "CORRESPONDENT_ATTORNEY",
        "ADVOCATE",
        "COURT",
        "SHERIFF",
        "MUNICIPALITY",
        "EXECUTOR",
        "BENEFICIARY",
        "SPOUSE",
        "ACCUSED",
        "COMPLAINANT"
    ]]]},
    {"dt": "Legal Forum", "filters": [["name", "in", [
        "CONSTITUTIONAL_COURT",
        "SUPREME_COURT_OF_APPEAL",
        "EASTERN_CAPE_HIGH_COURT_MAIN_SEAT_MAKHANDA",
        "EASTERN_CAPE_HIGH_COURT_LOCAL_SEAT_BHISHO",
        "EASTERN_CAPE_HIGH_COURT_LOCAL_SEAT_MTHATHA",
        "EASTERN_CAPE_HIGH_COURT_LOCAL_SEAT_GQEBERHA",
        "FREE_STATE_HIGH_COURT_BLOEMFONTEIN",
        "GAUTENG_HIGH_COURT_PRETORIA",
        "GAUTENG_HIGH_COURT_JOHANNESBURG",
        "KWAZULU_NATAL_HIGH_COURT_PIETERMARITZBURG",
        "KWAZULU_NATAL_HIGH_COURT_DURBAN",
        "LIMPOPO_HIGH_COURT_POLOKWANE",
        "LIMPOPO_HIGH_COURT_THOHOYANDOU",
        "LIMPOPO_HIGH_COURT_LEPHALALE",
        "MPUMALANGA_HIGH_COURT_MBOMBELA",
        "MPUMALANGA_HIGH_COURT_MIDDELBURG",
        "NORTH_WEST_HIGH_COURT_MAHIKENG",
        "NORTHERN_CAPE_HIGH_COURT_KIMBERLEY",
        "WESTERN_CAPE_HIGH_COURT_CAPE_TOWN",
        "LABOUR_APPEAL_COURT",
        "LABOUR_COURT_JOHANNESBURG",
        "LABOUR_COURT_CAPE_TOWN",
        "LABOUR_COURT_DURBAN",
        "LABOUR_COURT_GQEBERHA",
        "LAND_COURT",
        "LAND_CLAIMS_COURT",
        "ELECTORAL_COURT",
        "COMPETITION_APPEAL_COURT",
        "COMPETITION_TRIBUNAL",
        "TAX_COURT",
        "NATIONAL_CONSUMER_TRIBUNAL",
        "COMPANIES_TRIBUNAL",
        "EQUALITY_COURT",
        "SMALL_CLAIMS_COURT",
        "MAINTENANCE_COURT",
        "CHILDRENS_COURT",
        "DIVORCE_COURT",
        "CCMA_NATIONAL_OFFICE",
        "CCMA_EASTERN_CAPE",
        "CCMA_FREE_STATE",
        "CCMA_GAUTENG",
        "CCMA_KWAZULU_NATAL",
        "CCMA_LIMPOPO",
        "CCMA_MPUMALANGA",
        "CCMA_NORTH_WEST",
        "CCMA_NORTHERN_CAPE",
        "CCMA_WESTERN_CAPE",
        "EASTERN_CAPE_REGIONAL_MAGISTRATES_COURTS",
        "FREE_STATE_REGIONAL_MAGISTRATES_COURTS",
        "GAUTENG_REGIONAL_MAGISTRATES_COURTS",
        "KWAZULU_NATAL_REGIONAL_MAGISTRATES_COURTS",
        "LIMPOPO_REGIONAL_MAGISTRATES_COURTS",
        "MPUMALANGA_REGIONAL_MAGISTRATES_COURTS",
        "NORTH_WEST_REGIONAL_MAGISTRATES_COURTS",
        "NORTHERN_CAPE_REGIONAL_MAGISTRATES_COURTS",
        "WESTERN_CAPE_REGIONAL_MAGISTRATES_COURTS",
        "EASTERN_CAPE_DISTRICT_MAGISTRATES_COURTS",
        "FREE_STATE_DISTRICT_MAGISTRATES_COURTS",
        "GAUTENG_DISTRICT_MAGISTRATES_COURTS",
        "KWAZULU_NATAL_DISTRICT_MAGISTRATES_COURTS",
        "LIMPOPO_DISTRICT_MAGISTRATES_COURTS",
        "MPUMALANGA_DISTRICT_MAGISTRATES_COURTS",
        "NORTH_WEST_DISTRICT_MAGISTRATES_COURTS",
        "NORTHERN_CAPE_DISTRICT_MAGISTRATES_COURTS",
        "WESTERN_CAPE_DISTRICT_MAGISTRATES_COURTS"
    ]]]},
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/za_legal_practice/css/za_legal_practice.css"
# app_include_js = "/assets/za_legal_practice/js/za_legal_practice.js"

# include js, css files in header of web template
# web_include_css = "/assets/za_legal_practice/css/za_legal_practice.css"
# web_include_js = "/assets/za_legal_practice/js/za_legal_practice.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "za_legal_practice/public/scss/website"

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
app_include_icons = "/assets/za_legal_practice/images/za_legal_practice_logo.svg"

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
# 	"methods": "za_legal_practice.utils.jinja_methods",
# 	"filters": "za_legal_practice.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "za_legal_practice.install.before_install"
# after_install = "za_legal_practice.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "za_legal_practice.uninstall.before_uninstall"
# after_uninstall = "za_legal_practice.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "za_legal_practice.utils.before_app_install"
# after_app_install = "za_legal_practice.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "za_legal_practice.utils.before_app_uninstall"
# after_app_uninstall = "za_legal_practice.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "za_legal_practice.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "za_legal_practice.notifications.get_notification_config"

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
# 		"za_legal_practice.tasks.all"
# 	],
# 	"daily": [
# 		"za_legal_practice.tasks.daily"
# 	],
# 	"hourly": [
# 		"za_legal_practice.tasks.hourly"
# 	],
# 	"weekly": [
# 		"za_legal_practice.tasks.weekly"
# 	],
# 	"monthly": [
# 		"za_legal_practice.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "za_legal_practice.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "za_legal_practice.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "za_legal_practice.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "za_legal_practice.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["za_legal_practice.utils.before_request"]
# after_request = ["za_legal_practice.utils.after_request"]

# Job Events
# ----------
# before_job = ["za_legal_practice.utils.before_job"]
# after_job = ["za_legal_practice.utils.after_job"]

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
# 	"za_legal_practice.auth.validate"
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

