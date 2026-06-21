// Copyright (c) 2026, BuFf0k and contributors
// For license information, please see license.txt

frappe.ui.form.on("Legal Instrument", {
	refresh(frm) {
		frm.trigger("set_queries");
		frm.trigger("set_frbr_work_uri_preview");
	},

	jurisdiction(frm) {
		frm.trigger("set_frbr_work_uri_preview");
	},

	akn_doctype(frm) {
		frm.trigger("set_frbr_work_uri_preview");
	},

	year(frm) {
		frm.trigger("set_frbr_work_uri_preview");
	},

	number(frm) {
		frm.trigger("set_frbr_work_uri_preview");
	},

	set_queries(frm) {
		frm.set_query("jurisdiction", () => ({
			filters: {
				enabled: 1,
			},
		}));
	},

	set_frbr_work_uri_preview(frm) {
		const jurisdiction = (frm.doc.jurisdiction || "").trim().toLowerCase();
		const akn_doctype = (frm.doc.akn_doctype || "").trim();
		const year = frm.doc.year || "";
		const number = (frm.doc.number || "").toString().trim();

		if (!jurisdiction || !akn_doctype || !year || !number) {
			frm.set_value("frbr_work_uri", "");
			return;
		}

		frm.set_value("frbr_work_uri", `/akn/${jurisdiction}/${akn_doctype}/${year}/${number}`);
	},
});