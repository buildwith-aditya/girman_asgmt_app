import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import fmt_money


DEFAULT_80C_CAP = 150000
DEFAULT_80D_CAP = 50000
ENFORCE_CAPS = True

class EmployeeInvestmentDeclaration(Document):
    def validate(self):
        """
        Validate before saving:
         - required fields exist (DocType UI also enforces)
         - numeric fields are non-negative
         - compute total_exemption
         - prevent duplicates for same employee + fiscal_year (unless this doc is the same)
         - enforce statutory caps (configurable)
        """
        self._ensure_non_negative_amounts()
        self._compute_total_exemption()
        self._prevent_duplicate_declaration()
        self._enforce_statutory_caps()

    def _ensure_non_negative_amounts(self):
        for fn in ("section_80c_amount", "section_80d_amount", "other_exemptions"):
            value = self.get(fn) or 0
            try:
                value = float(value)
            except Exception:
                frappe.throw(_("{0} must be a number").format(self.meta.get_field(fn).label))
            if value < 0:
                frappe.throw(_("{0} cannot be negative").format(self.meta.get_field(fn).label))
            self.set(fn, value)

    def _compute_total_exemption(self):
        total = (self.section_80c_amount or 0.0) + (self.section_80d_amount or 0.0) + (self.other_exemptions or 0.0)
        self.total_exemption = frappe.utils.flt(total, 2)

    def _prevent_duplicate_declaration(self):
        """
        Prevent more than one declaration record for the same employee + fiscal_year
        unless the current doc is the same record (i.e., updating).
        """
        if not (self.employee and self.fiscal_year):
            frappe.throw(_("Both Employee and Fiscal Year are required"))

        existing = frappe.get_all(
            "Employee Investment Declaration",
            filters={
                "employee": self.employee,
                "fiscal_year": self.fiscal_year,
                "name": ("!=", self.name or "")
            },
            fields=["name", "owner", "creation"],
            limit=1
        )
        if existing:
            frappe.throw(_(
                "A declaration already exists for employee {0} in fiscal year {1}. "
                "Open {2} to update or delete it before creating a new one."
            ).format(self.employee, self.fiscal_year, existing[0].name))

    def _enforce_statutory_caps(self):
        """
        Optionally enforce caps. This function raises a validation error if values
        are above configured caps. If ENFORCE_CAPS is False, it only logs warnings.
        """
        errors = []
        warnings = []

        if DEFAULT_80C_CAP is not None and (self.section_80c_amount or 0.0) > DEFAULT_80C_CAP:
            msg = _("Section 80C declared amount ({0}) exceeds the cap of {1}.").format(
                fmt_money(self.section_80c_amount),
                fmt_money(DEFAULT_80C_CAP)
            )
            if ENFORCE_CAPS:
                errors.append(msg)
            else:
                warnings.append(msg)

        if DEFAULT_80D_CAP is not None and (self.section_80d_amount or 0.0) > DEFAULT_80D_CAP:
            msg = _("Section 80D declared amount ({0}) exceeds the cap of {1}.").format(
                fmt_money(self.section_80d_amount),
                fmt_money(DEFAULT_80D_CAP)
            )
            if ENFORCE_CAPS:
                errors.append(msg)
            else:
                warnings.append(msg)

        if errors:
            frappe.throw(_("Validation Error(s):\n") + "\n".join(errors))

        if warnings:
            for w in warnings:
                frappe.msgprint(w, title=_("Warning"), indicator="orange")


