import frappe
from frappe import _
from frappe.utils import flt, getdate

FALLBACK_REGIME_TO_STRUCTURE = {
    "Old Regime": "DEMO - Salary Structure - Old Regime",
    "New Regime": "DEMO - Salary Structure - New Regime",
}

def get_mapping_from_settings():
    mapping = FALLBACK_REGIME_TO_STRUCTURE.copy()
    return mapping

def _safe_get_amount_from_deduction_row(d):
    if isinstance(d, dict):
        return flt(d.get("amount") or d.get("deduction_amount") or 0.0)
    else:
        return flt(getattr(d, "amount", getattr(d, "deduction_amount", 0.0)))

def _safe_get_salary_component_name(d):
    if isinstance(d, dict):
        return (d.get("salary_component") or d.get("salary_component_name") or d.get("description") or "")
    else:
        return getattr(d, "salary_component", "") or getattr(d, "description", "")

def try_calculate_salary_slip(ss):
    if hasattr(ss, "set_earning_and_deduction"):
        try:
            ss.set_earning_and_deduction()
        except Exception:
            pass

    for method_name in ("calculate", "calculate_net_pay", "compute_net_pay", "compute_salary"):
        if hasattr(ss, method_name):
            try:
                getattr(ss, method_name)()
                return True
            except Exception:
                frappe.log_error(message=f"Salary Slip calc method {method_name} failed for in-memory slip for {ss.get('employee')}.", title="Tax Regime Report: calc error")
                continue

    if getattr(ss, "deductions", None):
        return True

    return False

def compute_tax_for_employee(employee, salary_structure_name, start_date, end_date):
    """
    Build an in-memory Salary Slip for employee + structure for the given date range,
    run calculation, and return aggregated tax deduction.

    This version is defensive: validates inputs and logs context for easier debugging.
    """
    if not salary_structure_name:
        frappe.throw(_("Salary Structure not configured for regime used in report. Please configure mapping or check salary structure names."))
        return 0.0

    from frappe.utils import getdate, add_months, get_last_day
    try:
        sd = getdate(start_date)
    except Exception:
        frappe.throw(_("Invalid start date passed to compute_tax_for_employee: {0}").format(start_date))

    if not end_date:
        end_date = get_last_day(sd)
    try:
        ed = getdate(end_date)
    except Exception:
        frappe.throw(_("Invalid end date passed to compute_tax_for_employee: {0}").format(end_date))

    if sd > ed:
        frappe.throw(_("Start date {0} is after end date {1} for employee {2}.").format(sd, ed, employee))

    try:
        company = frappe.get_value("Employee", employee, "company") or frappe.get_single("Global Defaults").default_company
    except Exception:
        company = None

    slip_doc = {
        "employee": employee,
        "salary_structure": salary_structure_name,
        "start_date": sd,
        "end_date": ed,
        "company": company
    }

    try:
        ss = frappe.get_doc("Salary Slip", slip_doc)
    except Exception as e:
        frappe.log_error(message=f"Failed to construct in-memory Salary Slip for {employee} / {salary_structure_name}: {e}", title="Tax Regime Report: doc creation failed")
        return 0.0

    tax_amount = 0.0
    for d in getattr(ss, "deductions", []) or []:
        comp_name = (_safe_get_salary_component_name(d) or "").lower()
        amt = _safe_get_amount_from_deduction_row(d)
        if any(k in comp_name for k in ("tax", "tds", "income tax", "professional tax")):
            tax_amount += flt(amt)

    if flt(tax_amount) == 0.0:
        for d in getattr(ss, "deductions", []) or []:
            comp_name = (_safe_get_salary_component_name(d) or "").lower()
            if "income" in comp_name:
                tax_amount += _safe_get_amount_from_deduction_row(d)

    return flt(tax_amount)


def execute(filters=None):
    """
    Script report entrypoint called by ERPNext.
    Filters required: from_date, to_date
    Optional filters: company, employee, department
    """
    if filters is None:
        filters = {}

    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw(_("Please select From Date and To Date (both are mandatory)."))

    try:
        from_date = getdate(filters.get("from_date"))
        to_date = getdate(filters.get("to_date"))
    except Exception:
        frappe.throw(_("Invalid date format for From Date / To Date."))

    if from_date > to_date:
        frappe.throw(_("From Date cannot be after To Date."))

    mapping = get_mapping_from_settings()
    old_structure = mapping.get("Old Regime")
    new_structure = mapping.get("New Regime")

    columns = [
        _("Employee") + ":Link/Employee:120",
        _("Employee Name") + "::160",
        _("Company") + ":Link/Company:140",
        _("Tax (Old)") + ":Currency:120",
        _("Tax (New)") + ":Currency:120",
        _("Difference (Old - New)") + ":Currency:120",
        _("Recommended") + "::120",
    ]

    emp_filters = {}
    if filters.get("company"):
        emp_filters["company"] = filters.get("company")
    if filters.get("employee"):
        emp_filters["name"] = filters.get("employee")
    if filters.get("department"):
        emp_filters["department"] = filters.get("department")

    employees = frappe.get_all("Employee", filters=emp_filters, fields=["name", "employee_name", "company"], limit_page_length=1000)

    data = []
    for e in employees:
        try:
            old_tax = compute_tax_for_employee(e["name"], old_structure, from_date, to_date)
            new_tax = compute_tax_for_employee(e["name"], new_structure, from_date, to_date)
            diff = flt(old_tax) - flt(new_tax)
            recommended = "New Regime" if diff > 0 else "Old Regime"
            data.append([e["name"], e.get("employee_name"), e.get("company"), old_tax, new_tax, diff, recommended])
        except Exception as exc:
            frappe.log_error(message=f"Tax Regime comparison error for employee {e.get('name')}: {exc}", title="Tax Regime Report: compute error")
            data.append([e["name"], e.get("employee_name"), e.get("company"), _("Error"), _("Error"), _("Error"), _("Error")])

    return columns, data
