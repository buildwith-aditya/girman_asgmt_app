# girman_assgn_app/girman_hr/tax_regime.py
import frappe
from frappe import _

# Minimal hardcoded mapping. Use exact Salary Structure names you created.
REGIME_TO_STRUCTURE = {
    "Old Regime": "DEMO - Salary Structure - Old Regime",
    "New Regime": "DEMO - Salary Structure - New Regime"
}
ALLOWED_STRUCTURES = set(REGIME_TO_STRUCTURE.values())


def validate_salary_structure_assignment(doc, method=None):
    """
    Ensure Salary Structure Assignment uses only allowed regime salary structures.
    Raises helpful error if user picks other structures.
    """
    # doc.salary_structure is the linked salary structure in the assignment
    ss = doc.get("salary_structure")
    if not ss:
        # If no salary structure selected, permit (or throw depending on policy). We'll allow empty.
        return

    if ss not in ALLOWED_STRUCTURES:
        # Provide clear error + hint how to fix.
        allowed_list = ", ".join(sorted(ALLOWED_STRUCTURES))
        frappe.throw(
            _("Salary Structure Assignment may only reference salary structures for Old/New tax regimes. "
              "Found: {ss}. Please choose one of: {allowed}").format(ss=ss, allowed=allowed_list)
        )
