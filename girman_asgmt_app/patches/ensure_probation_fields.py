import frappe

def execute():
    """
    1) Ensure HR Settings single has default_probation_days (Int)
    2) Ensure Employee has probation_start, probation_end, confirmation_date (Date)
    """
    ensure_hr_setting_field()
    ensure_employee_fields()

def ensure_hr_setting_field():
    doctype = "HR Settings"
    fieldname = "default_probation_days"
    if not field_exists(doctype, fieldname):
        print(f"Adding field {fieldname} to {doctype}")
        add_field_customize(doctype,
            dict(fieldname=fieldname,
                 label="Default Probation Days",
                 fieldtype="Int",
                 insert_after="retirement_age",
                 default="90")
        )
        # set default value on Single doc if not present
        try:
            hr = frappe.get_single("HR Settings")
            if not hr.get(fieldname):
                hr.set(fieldname, 90)
                hr.save(ignore_permissions=True)
                frappe.db.commit()
        except Exception:
            pass
    else:
        print(f"{doctype}.{fieldname} exists")

def ensure_employee_fields():
    doctype = "Employee"
    fields = [
        dict(fieldname="probation_start", label="Probation Start", fieldtype="Date", insert_after="date_of_joining"),
        dict(fieldname="probation_end", label="Probation End", fieldtype="Date", insert_after="probation_start"),
        dict(fieldname="lifecycle_status", label="Lifecycle Status", fieldtype="Select", insert_after="status", options="\nProbation\nConfirmed\nExited"),
        dict(fieldname="experience_letter", label="Experience Letter", fieldtype="Attach", insert_after="leave_encashed"),
    ]
    for f in fields:
        if not field_exists(doctype, f["fieldname"]):
            print(f"Adding field {f['fieldname']} to {doctype}")
            add_field_customize(doctype, f)
        else:
            print(f"{doctype}.{f['fieldname']} exists")

# utility helpers
def field_exists(doctype, fieldname):
    try:
        meta = frappe.get_meta(doctype)
        return any(f.fieldname == fieldname for f in meta.fields)
    except Exception:
        # fallback: check Customize Form
        return bool(frappe.db.get_value("Custom Field", {"dt": doctype, "fieldname": fieldname}))

def add_field_customize(doctype, field_dict):
    """
    Use Customize Form pattern to add a field. field_dict must contain:
      fieldname, label, fieldtype, optional insert_after, options, default
    """
    cf = frappe.get_doc({
        "doctype":"Customize Form",
        "dt": doctype,
        "fieldname": field_dict["fieldname"],
        "fieldtype": field_dict["fieldtype"],
        "label": field_dict.get("label") or field_dict["fieldname"],
        "insert_after": field_dict.get("insert_after") or "",
        "options": field_dict.get("options") or "",
        "default": field_dict.get("default") or ""
    })
    try:
        cf.save()
        frappe.db.commit()
    except Exception:
        # fallback: create as Custom Field directly
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": doctype,
            **field_dict
        }).insert(ignore_permissions=True)
        frappe.db.commit()
