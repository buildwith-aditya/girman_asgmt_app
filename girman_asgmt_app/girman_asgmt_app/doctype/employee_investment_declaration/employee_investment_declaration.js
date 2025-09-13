frappe.ui.form.on("Employee Investment Declaration", {
    refresh: function(frm) {
        frm.set_df_property("total_exemption", "read_only", 1);
        frm.set_intro("Enter employee investment amounts for the selected fiscal year. Total is auto-calculated.");

        // recompute on refresh (useful when form is loaded)
        compute_total(frm);
    },

    section_80c_amount: function(frm) { compute_total(frm); },
    section_80d_amount: function(frm) { compute_total(frm); },
    other_exemptions: function(frm) { compute_total(frm); },

});

function compute_total(frm) {
    const a = flt(frm.doc.section_80c_amount, 2);
    const b = flt(frm.doc.section_80d_amount, 2);
    const c = flt(frm.doc.other_exemptions, 2);
    const total = flt(a + b + c, 2);

    frm.set_value("total_exemption", total);

    const CAP_80C = 150000;
    const CAP_80D = 50000;
    let warn_messages = [];
    if (a > CAP_80C) warn_messages.push(`80C exceeds cap ${format_currency(CAP_80C)}`);
    if (b > CAP_80D) warn_messages.push(`80D exceeds cap ${format_currency(CAP_80D)}`);

    if (warn_messages.length) {
        if (frm.dashboard && frm.dashboard.show_headline) {
            frm.dashboard.show_headline(warn_messages.join(" • "));
        } else {
            frappe.msgprint({message: warn_messages.join("<br>"), title: "Warning", indicator: "orange"});
        }
    } else {
        if (frm.dashboard && frm.dashboard.clear_headline) {
            frm.dashboard.clear_headline();
        }
    }
}

function flt(v, precision) {
    v = parseFloat(v || 0);
    if (isNaN(v)) v = 0;
    if (typeof precision !== "undefined") {
        const pow = Math.pow(10, precision);
        v = Math.round(v * pow) / pow;
    }
    return v;
}

function format_currency(v) {
    if (frappe && frappe.format && frappe.meta) {
        return frappe.format(v, {fieldtype: "Currency"});
    }
    if (window.format_currency) {
        return window.format_currency(v);
    }
    return v.toString();
}


