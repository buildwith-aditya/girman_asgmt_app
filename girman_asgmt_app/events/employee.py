import frappe
from frappe.utils import add_days, getdate, nowdate

# ----------------------------
# Configuration / constants
# ----------------------------
DEFAULT_PROBATION_DAYS = 90


# ----------------------------
# Helpers
# ----------------------------
def _get_default_probation_days() -> int:
    """Return probation days from HR Settings, or fallback to DEFAULT_PROBATION_DAYS."""
    try:
        hr = frappe.get_single("HR Settings")
        val = hr.get("default_probation_days") or hr.get("probation_period")
        return int(val) if val else DEFAULT_PROBATION_DAYS
    except Exception:
        return DEFAULT_PROBATION_DAYS


def _compute_probation_dates(doj, probation_days: int):
    """
    Compute (probation_start, probation_end, confirmation_date).
    probation_end is inclusive. confirmation_date is the day after the last probation day.
    """
    doj = doj or nowdate()
    start = getdate(doj)
    end = add_days(start, probation_days - 1)
    confirmation = add_days(start, probation_days)
    return start, end, confirmation


def _safe_db_set(doc, field: str, value):
    """Set a field using db_set when available; fallback to frappe.db.set_value."""
    try:
        if hasattr(doc, "db_set"):
            doc.db_set(field, value)
        else:
            frappe.db.set_value(doc.doctype, doc.name, field, value)
    except Exception:
        try:
            frappe.db.set_value(doc.doctype, doc.name, field, value)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "employee._safe_db_set")


# ----------------------------
# Event handlers
# ----------------------------
def on_employee_after_insert(doc, method=None):
    """Populate probation fields when an Employee is created."""
    try:
        days = _get_default_probation_days()
        ps, pe, conf = _compute_probation_dates(doc.get("date_of_joining"), days)
        _safe_db_set(doc, "probation_start", ps)
        _safe_db_set(doc, "probation_end", pe)
        if not doc.get("final_confirmation_date"):
            _safe_db_set(doc, "final_confirmation_date", conf)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "employee.on_employee_after_insert")


def on_employee_on_update(doc, method=None):
    """
    On update:
      - Recompute probation dates if date_of_joining changed or probation fields missing.
      - Respond to lifecycle transitions: Confirmed / Exited.
    """
    try:
        prev = frappe.get_doc(doc.doctype, doc.name)

        doj_changed = bool(prev and prev.get("date_of_joining") != doc.get("date_of_joining"))
        probation_missing = not (doc.get("probation_start") and doc.get("probation_end") and doc.get("final_confirmation_date"))

        if doj_changed or probation_missing:
            days = _get_default_probation_days()
            ps, pe, conf = _compute_probation_dates(doc.get("date_of_joining"), days)
            _safe_db_set(doc, "probation_start", ps)
            _safe_db_set(doc, "probation_end", pe)
            if doj_changed or not doc.get("final_confirmation_date"):
                _safe_db_set(doc, "final_confirmation_date", conf)

        new_status = doc.get("lifecycle_status")
        if new_status == "Confirmed":
            _handle_confirmed(doc)
        elif new_status == "Exited":
            _handle_exited(doc)

    except Exception:
        frappe.log_error(frappe.get_traceback(), "employee.on_employee_on_update")


def on_employee_after_save(doc, method=None):
    """
    Safety net for workflows: ensure confirmation/exit handlers applied
    when states have already changed via workflow actions.
    """
    try:
        if doc.get("lifecycle_status") == "Confirmed" and not doc.get("final_confirmation_date"):
            _handle_confirmed(doc)

        if doc.get("lifecycle_status") == "Exited" and not doc.get("relieving_date"):
            _handle_exited(doc)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "employee.on_employee_after_save")


# ----------------------------
# Lifecycle handlers
# ----------------------------
def _handle_confirmed(doc):
    """Actions to run when employee is confirmed."""
    try:
        if not doc.get("final_confirmation_date"):
            _safe_db_set(doc, "final_confirmation_date", nowdate())
        _safe_db_set(doc, "status", "Active")
    except Exception:
        frappe.log_error(frappe.get_traceback(), "employee._handle_confirmed")


def _handle_exited(doc):
    """Actions to run when employee exits."""
    try:
        if not doc.get("relieving_date"):
            _safe_db_set(doc, "relieving_date", nowdate())
        _safe_db_set(doc, "status", "Left")

    except Exception:
        frappe.log_error(frappe.get_traceback(), "employee._handle_exited")

