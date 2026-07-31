app_name = "ebics_bank_connector"
app_title = "EBICS Bank Connector"
app_publisher = "h4ppii"
app_description = "EBICS banking automation for ERPNext 16 (VR-Bank NordRhön eG and other EBICS banks)"
app_email = ""
app_license = "GPL-3.0-or-later"

required_apps = ["erpnext"]

# ------------------------------------------------------------------
# Installation
# ------------------------------------------------------------------
before_install = "ebics_bank_connector.install.before_install"
after_install = "ebics_bank_connector.install.after_install"

# ------------------------------------------------------------------
# DocTypes
# ------------------------------------------------------------------
# (auto-discovered from the module folder)

# ------------------------------------------------------------------
# Page / Wizard
# ------------------------------------------------------------------
# pages are auto-discovered; the Banking Setup Wizard lives under
# ebics_bank_connector/ebics_bank_connector/page/banking_setup_wizard

# ------------------------------------------------------------------
# Scheduler
# ------------------------------------------------------------------
scheduler_events = {
    "hourly": [
        "ebics_bank_connector.sync.run_hourly_sync"
    ],
    "daily": [
        "ebics_bank_connector.sync.run_daily_sync",
        "ebics_bank_connector.sync.cleanup_old_xml",
        "ebics_bank_connector.monitoring.run_daily_monitoring"
    ],
}

# ------------------------------------------------------------------
# Boot session: expose minimal status to the desk client
# ------------------------------------------------------------------
boot_session = "ebics_bank_connector.utils.boot_session"

# ------------------------------------------------------------------
# User Protection / roles
# ------------------------------------------------------------------
# Standard roles are created via fixtures on install (see install.py)

# ------------------------------------------------------------------
# Website / portal (not used)
# ------------------------------------------------------------------

# ------------------------------------------------------------------
# Fixed assets / fixtures: roles + custom fields are exported on install
# ------------------------------------------------------------------
fixtures = [
    {"dt": "Role", "filters": [["name", "in", ["Bank Administrator", "Bank Buchhalter", "Bank Mitarbeiter"]]]},
]

# ------------------------------------------------------------------
# Permission query / doctype permissions are defined inline in doctypes
# ------------------------------------------------------------------

# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------
# error shown in error log via standard frappe logger
