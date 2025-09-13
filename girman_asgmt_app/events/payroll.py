import frappe
from datetime import date
from frappe.utils import getdate
from frappe import _

INVESTMENT_COMPONENT = "Investment Exemption"


def get_total_declarations(employee: str, fiscal_year: str) -> float:
    """Return total exemption for employee and fiscal_year (sum of total_exemption)."""
    if not employee or not fiscal_year:
        return 0.0
    res = frappe.get_all(
        "Employee Investment Declaration",
        filters={"employee": employee, "fiscal_year": fiscal_year},
        fields=["total_exemption"]
    )
    total = res and res[0].get("total_exemption") or 0.0
    return float(total or 0.0)


def ensure_investment_component_exists():
    """Create the Salary Component if it doesn't exist."""
    if frappe.db.exists("Salary Component", {"salary_component": INVESTMENT_COMPONENT}):
        return
    doc = frappe.get_doc({
        "doctype": "Salary Component",
        "salary_component": INVESTMENT_COMPONENT,
        "component_type": "Deduction",
        "salary_component_abbr": "INV_EXEMPT",
        "is_taxable": 0,
        "default_amount": 0
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()


def _fiscal_year_from_date(dt) -> str:
    """
    Given a date (datetime.date or string), return fiscal year string like '2025-26'.
    Assumes Indian FY Apr (4) -> Mar (3) next year.
    """
    if not dt:
        dt = date.today()
    else:
        try:
            dt = getdate(dt)
        except Exception:
            dt = date.today()

    year = dt.year
    start_year = year if dt.month >= 4 else year - 1
    end_year = str(start_year + 1)
    fy = f"{start_year}-{end_year}"
    return fy


def _parse_fiscal_year_start(fiscal_year: str) -> int:
    """
    Parse fiscal_year like '2025-26' or '2025-2026' and return the starting year as int.
    Fallback: current year.
    """
    if not fiscal_year:
        return date.today().year
    try:
        part = fiscal_year.split("-")[0]
        return int(part)
    except Exception:
        try:
            return int(fiscal_year[:4])
        except Exception:
            return date.today().year


def months_remaining_in_fiscal(slip_start_date, fiscal_year=None) -> int:
    """
    Compute remaining months in the fiscal year including the month of slip_start_date.
    If fiscal_year is None, derive it from slip_start_date.
    Returns an integer between 1 and 12.
    """
    if not slip_start_date:
        return 12

    try:
        sd = getdate(slip_start_date)
    except Exception:
        sd = date.today()
    if not fiscal_year:
        fiscal_year = _fiscal_year_from_date(sd)
    start_year = _parse_fiscal_year_start(fiscal_year)
    fiscal_end_year = start_year + 1
    fiscal_end_month = 3  # March
    months = (fiscal_end_year - sd.year) * 12 + (fiscal_end_month - sd.month) + 1
    if months < 1:
        months = 1
    if months > 12:
        months = 12
    return months


def remove_existing_investment_row(salary_slip):
    """Remove any existing Investment Exemption rows from salary_slip.deductions to avoid duplication."""
    if not getattr(salary_slip, "get", None):
        return
    deductions = salary_slip.get("deductions") or []
    new_rows = []
    removed = False
    for d in deductions:
        comp = d.get("salary_component") if isinstance(d, dict) else getattr(d, "salary_component", None)
        if comp == INVESTMENT_COMPONENT:
            removed = True
            continue
        new_rows.append(d.as_dict() if hasattr(d, "as_dict") else d)
    if removed:
        salary_slip.set("deductions", [])
        for r in new_rows:
            salary_slip.append("deductions", r)


def add_investment_deduction_row(salary_slip, amount):
    """Add or update the Investment Exemption row in salary_slip.deductions."""
    if not amount or float(amount) <= 0:
        return
    for d in salary_slip.get("deductions") or []:
        comp = d.get("salary_component") if isinstance(d, dict) else getattr(d, "salary_component", None)
        if comp == INVESTMENT_COMPONENT:
            if isinstance(d, dict):
                d["amount"] = amount
            else:
                d.amount = amount
            return
    salary_slip.append("deductions", {
        "salary_component": INVESTMENT_COMPONENT,
        "abbr": "INV_EXEMPT",
        "amount": amount
    })


def adjust_salary_slip_with_investments(salary_slip, method=None):
    """
    Hook: runs on Salary Slip validate.
    Behavior:
      - Reads Employee Investment Declaration total for the employee & fiscal_year (derived if needed)
      - Ensures the Salary Component exists
      - Removes previous Investment Exemption row (if any)
      - Pro-rates the total across remaining months in the fiscal year and adds per_month amount as a deduction
    """
    try:
        employee = salary_slip.get("employee") if hasattr(salary_slip, "get") else getattr(salary_slip, "employee", None)
        start_date = salary_slip.get("start_date") if hasattr(salary_slip, "get") else getattr(salary_slip, "start_date", None)
        fiscal_year = salary_slip.get("fiscal_year") if hasattr(salary_slip, "get") else getattr(salary_slip, "fiscal_year", None)
        
        if not employee:
            return

        if not fiscal_year:
            fiscal_year = _fiscal_year_from_date(start_date)
        total = get_total_declarations(employee, fiscal_year)

        ensure_investment_component_exists()

        remove_existing_investment_row(salary_slip)

        if not total or float(total) <= 0:
            return
        months = months_remaining_in_fiscal(start_date, fiscal_year) or 12
        per_month = float(total) / float(months)
        per_month = round(per_month, 2)

        add_investment_deduction_row(salary_slip, per_month)

    except Exception as err:
        frappe.log_error(message=frappe.get_traceback(), title="adjust_salary_slip_with_investments")
        raise
