import frappe

def execute():
    df = {
        "doctype":"Custom Field",
        "dt":"Employee",
        "fieldname":"tax_regime_preference",
        "label":"Tax Regime Preference",
        "fieldtype":"Select",
        "options":"Old Regime\nNew Regime",
        "insert_after":"employment_type",
        "in_list_view":1,
        "default":"Old Regime",
        "description":"Pick tax regime preference for payroll"
    }
    if not frappe.db.exists("Custom Field", {"dt":"Employee", "fieldname":"tax_regime_preference"}):
        frappe.get_doc(df).insert(ignore_permissions=True)
