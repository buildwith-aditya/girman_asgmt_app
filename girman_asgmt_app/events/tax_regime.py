import frappe
from frappe import _

REGIME_TO_STRUCTURE = {
    "Old Regime": "DEMO - Salary Structure - Old Regime",
    "New Regime": "DEMO - Salary Structure - New Regime"
}
ALLOWED_STRUCTURES = set(REGIME_TO_STRUCTURE.values())

def get_employee_regime(employee):
    """Return the value of tax_regime_preference for employee, fallback to Old Regime."""
    if not employee:
        return None
    emp = frappe.get_cached_doc("Employee", employee)
    return emp.get("tax_regime_preference") or "Old Regime"

def set_salary_structure_for_employee(doc, method=None):
    """
    Hook: before_insert on Salary Slip.
    Sets doc.salary_structure based on employee tax regime preference.
    """
    if not getattr(doc, "employee", None):
        return
    regime = get_employee_regime(doc.employee)

    expected_structure = REGIME_TO_STRUCTURE.get(regime)

    if not expected_structure:
        frappe.log_error(message=f"Unknown mapping for tax regime: {regime}", title="Tax Regime Mapping Missing")
        return

    current_structure = doc.get("salary_structure")
    if not current_structure or current_structure != expected_structure:
        doc.salary_structure = expected_structure

        # Clear earnings and deductions so calculation repopulates
        try:
            if hasattr(doc, "earnings"):
                doc.earnings = []
            if hasattr(doc, "deductions"):
                doc.deductions = []
        except Exception as e:
            frappe.log_error(message=str(e), title="Error Clearing Salary Slip Tables")
    else:
        frappe.log_error(message="Salary structure already correct. No changes made.", title="Salary Structure Already Correct")


def ensure_salary_structure_matches_regime(doc, method=None):
    """Hook: validate on Salary Slip. Prevent mismatched structure vs employee preference."""
    if not getattr(doc, "employee", None):
        return

    regime = get_employee_regime(doc.employee)
    expected_structure = REGIME_TO_STRUCTURE.get(regime)

    if expected_structure and doc.get("salary_structure") and doc.get("salary_structure") != expected_structure:
        frappe.throw(_("Salary Structure '{0}' does not match employee {1}'s Tax Regime Preference ({2}). Expected: {3}")
                     .format(doc.get("salary_structure"), doc.employee, regime, expected_structure))


def ensure_payroll_slips_match_regime(payroll_doc, method=None):
    """
    Iterate payroll entries' employee list (or created Salary Slips) and ensure salary_structure set.
    This runs before Payroll Entry submit — it attempts to update any not-yet-created or pre-created slips.
    """
    emp_list = []
    if hasattr(payroll_doc, "employees"):
        emp_list = [r.employee for r in getattr(payroll_doc, "employees") or []]
    elif getattr(payroll_doc, "employee", None):
        emp_list = [payroll_doc.employee]

    for emp in emp_list:
        regime = get_employee_regime(emp)
        expected = REGIME_TO_STRUCTURE.get(regime)
        ss_list = frappe.get_all("Salary Slip",
                                filters={"employee": emp, "docstatus": 0, "payroll_entry": payroll_doc.name},
                                fields=["name"])
        for ss in ss_list:
            frappe.db.set_value("Salary Slip", ss.name, "salary_structure", expected)


def validate_salary_structure_assignment(doc, method=None):
    """
    Ensure Salary Structure Assignment uses only allowed regime salary structures.
    Raises helpful error if user picks other structures.
    """
    ss = doc.get("salary_structure")
    if not ss:
        return

    if ss not in ALLOWED_STRUCTURES:
        allowed_list = ", ".join(sorted(ALLOWED_STRUCTURES))
        frappe.throw(
            _("Salary Structure Assignment may only reference salary structures for Old/New tax regimes. "
              "Found: {ss}. Please choose one of: {allowed}").format(ss=ss, allowed=allowed_list)
        )
