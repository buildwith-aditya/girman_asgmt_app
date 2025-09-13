frappe.ui.form.off("Salary Structure Assignment", "employee");
frappe.ui.form.on("Salary Structure Assignment", {
	employee: async function (frm) {
		if (frm.doc.employee) {
			frm.trigger("set_payroll_cost_centers");
			frm.trigger("toggle_opening_balances_section");

			const employee_regime = await frappe.db.get_value(
				"Employee",
				frm.doc.employee,
				"tax_regime_preference"
			);

			if (!employee_regime) return;
			const filter_salary_structure = [
				"like",
				"%" + employee_regime.message.tax_regime_preference + "%",
			];
			frm.set_query("salary_structure", function () {
				return {
					filters: {
						name: filter_salary_structure,
					},
				};
			});
		} else {
			frm.set_value("payroll_cost_centers", []);
		}
	},
});
