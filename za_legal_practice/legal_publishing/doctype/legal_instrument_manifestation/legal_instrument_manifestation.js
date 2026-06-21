// Copyright (c) 2026, BuFf0k and contributors
// For license information, please see license.txt

frappe.ui.form.on("Legal Instrument Manifestation", {
	refresh(frm) {
		frm.trigger("set_queries");
		add_custom_buttons(frm);
	},

	legal_instrument(frm) {
		if (frm.doc.expression) {
			frm.set_value("expression", null);
		}
	},

	set_queries(frm) {
		frm.set_query("legal_instrument", () => ({
			filters: {
				status: ["!=", "Archived"],
			},
		}));

		frm.set_query("expression", () => {
			const filters = {};

			if (frm.doc.legal_instrument) {
				filters.legal_instrument = frm.doc.legal_instrument;
			}

			return { filters };
		});
	},
});

function add_custom_buttons(frm) {
	if (frm.is_new()) {
		return;
	}

	if (frm.doc.expression) {
		frm.add_custom_button(__("Open Expression"), () => {
			frappe.set_route("Form", "Legal Instrument Expression", frm.doc.expression);
		}, __("Legal Publishing"));
	}

	if (frm.doc.ocr_job) {
		frm.add_custom_button(__("Open OCR Job"), () => {
			frappe.set_route("Form", "Legal OCR Job", frm.doc.ocr_job);
		}, __("OCR"));
		return;
	}

	if (frm.doc.file && frm.doc.manifestation_type === "Source PDF") {
		frm.add_custom_button(__("Create OCR Job"), () => {
			frappe.call({
				method: "za_legal_practice.legal_publishing.doctype.legal_instrument_manifestation.legal_instrument_manifestation.create_ocr_job",
				args: {
					source_manifestation: frm.doc.name,
				},
				freeze: true,
				freeze_message: __("Creating OCR Job..."),
				callback(r) {
					if (!r.message) {
						return;
					}

					frm.reload_doc().then(() => {
						frappe.set_route("Form", "Legal OCR Job", r.message);
					});
				},
			});
		}, __("OCR"));
	}
}