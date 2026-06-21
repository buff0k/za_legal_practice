// Copyright (c) 2026, BuFf0k and contributors
// For license information, please see license.txt

frappe.ui.form.on("Legal Amendment", {
	refresh(frm) {
		frm.trigger("set_queries");
	},

	set_queries(frm) {
		if (frm.fields_dict.legal_instrument) {
			frm.set_query("legal_instrument", () => ({
				filters: {
					status: ["!=", "Archived"],
				},
			}));
		}

		if (frm.fields_dict.target_instrument) {
			frm.set_query("target_instrument", () => ({
				filters: {
					status: ["!=", "Archived"],
				},
			}));
		}

		if (frm.fields_dict.amending_instrument) {
			frm.set_query("amending_instrument", () => ({
				filters: {
					status: ["!=", "Archived"],
				},
			}));
		}
	},
});
