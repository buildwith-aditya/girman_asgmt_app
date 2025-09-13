
frappe.query_reports["Tax Regime Comparison"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "reqd": 1
        },
        {
            "fieldname": "company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company",
            "default": frappe.defaults.get_default("company") || ""
        },
        {
            "fieldname": "department",
            "label": __("Department"),
            "fieldtype": "Link",
            "options": "Department"
        },
        {
            "fieldname": "employee",
            "label": __("Employee"),
            "fieldtype": "Link",
            "options": "Employee"
        }
    ],

    onload: function(report) {
        report.page.add_inner_button(__("Run Comparison"), function() {
            const f = report.get_values();
            if (!f || !f.from_date || !f.to_date) {
                frappe.msgprint({ title: __("Missing dates"), message: __("Please select both From Date and To Date before running the report."), indicator: "red" });
                return;
            }
            if (f.from_date > f.to_date) {
                frappe.msgprint({ title: __("Invalid range"), message: __("From Date cannot be after To Date."), indicator: "red" });
                return;
            }
            report.refresh();
        });
    },

    formatter: function(value, row, column, data, default_formatter) {
        try {
            const recommended = data && data[data.length - 1];
            if (recommended && column && (column.label || "").toLowerCase().includes("recommended")) {
                if (recommended === "New Regime") {
                    return `<span style='color:green; font-weight:600'>${__(recommended)}</span>`;
                } else {
                    return `<span style='color:blue; font-weight:600'>${__(recommended)}</span>`;
                }
            }

            if ((column.label || "").toLowerCase().includes("difference")) {
                let v = parseFloat(value) || 0;
                if (v > 0) {
                    return `<span style="color: #d9534f; font-weight:600">${value}</span>`;
                } else if (v < 0) {
                    return `<span style="color: #5cb85c; font-weight:600">${value}</span>`;
                }
            }
        } catch (e) {
            // ignore and fallback
        }
        return default_formatter(value, row, column, data);
    }
};
