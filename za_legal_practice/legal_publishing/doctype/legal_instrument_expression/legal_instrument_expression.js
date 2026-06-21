// Copyright (c) 2026, BuFf0k and contributors
// For license information, please see license.txt

frappe.ui.form.on("Legal Instrument Expression", {
	refresh(frm) {
		frm.trigger("set_queries");
		frm.trigger("set_frbr_expression_uri_preview");
		add_custom_buttons(frm);
	},

	legal_instrument(frm) {
		frm.trigger("set_frbr_expression_uri_preview");
		frm.trigger("set_expression_title_if_missing");
	},

	language(frm) {
		frm.trigger("set_frbr_expression_uri_preview");
		frm.trigger("set_expression_title_if_missing");
	},

	expression_date(frm) {
		frm.trigger("set_frbr_expression_uri_preview");
		frm.trigger("set_expression_title_if_missing");
	},

	version_label(frm) {
		frm.trigger("set_expression_title_if_missing");
	},

	set_queries(frm) {
		frm.set_query("legal_instrument", () => ({
			filters: {
				status: ["!=", "Archived"],
			},
		}));
	},

	set_frbr_expression_uri_preview(frm) {
		if (!frm.doc.legal_instrument || !frm.doc.language || !frm.doc.expression_date) {
			frm.set_value("frbr_expression_uri", "");
			return;
		}

		frappe.db.get_value(
			"Legal Instrument",
			frm.doc.legal_instrument,
			["frbr_work_uri", "instrument_title"]
		).then((result) => {
			const values = result.message || {};
			const frbr_work_uri = values.frbr_work_uri;

			if (!frbr_work_uri) {
				frm.set_value("frbr_expression_uri", "");
				return;
			}

			const language_code = get_akn_language_code(frm.doc.language);
			const expression_date = frm.doc.expression_date;

			frm.set_value(
				"frbr_expression_uri",
				`${frbr_work_uri.replace(/\/$/, "")}/${language_code}@${expression_date}`
			);
		});
	},

	set_expression_title_if_missing(frm) {
		if (frm.doc.expression_title || !frm.doc.legal_instrument || !frm.doc.language || !frm.doc.expression_date) {
			return;
		}

		frappe.db.get_value(
			"Legal Instrument",
			frm.doc.legal_instrument,
			"instrument_title"
		).then((result) => {
			const instrument_title = result.message && result.message.instrument_title;

			if (!instrument_title) {
				return;
			}

			const language_code = get_akn_language_code(frm.doc.language);
			const version_label = frm.doc.version_label || frm.doc.expression_date;

			frm.set_value(
				"expression_title",
				`${instrument_title} - ${language_code} - ${version_label}`
			);
		});
	},
});

function add_custom_buttons(frm) {
	if (frm.is_new()) {
		return;
	}

	frm.add_custom_button(__("Create Source PDF Manifestation"), () => {
		frappe.new_doc("Legal Instrument Manifestation", {
			legal_instrument: frm.doc.legal_instrument,
			expression: frm.doc.name,
			manifestation_type: "Source PDF",
			ocr_required: 1,
		});
	}, __("Legal Publishing"));

	frm.add_custom_button(__("View Manifestations"), () => {
		frappe.set_route("List", "Legal Instrument Manifestation", {
			expression: frm.doc.name,
		});
	}, __("Legal Publishing"));

	if (frm.doc.bluebell_text) {
		frm.add_custom_button(__("Clean OCR Text"), () => {
			frappe.confirm(
				__("Clean the current Bluebell Text? This will replace the existing text with a cleaned version."),
				() => {
					frappe.call({
						method: "za_legal_practice.legal_publishing.doctype.legal_instrument_expression.legal_instrument_expression.clean_ocr_text",
						args: {
							expression: frm.doc.name,
							replace_existing: 1,
						},
						freeze: true,
						freeze_message: __("Cleaning OCR text..."),
						callback(r) {
							if (!r.message) {
								return;
							}

							frappe.show_alert({
								message: __(
									"Cleaned text. Original: {0} chars, cleaned: {1} chars.",
									[
										r.message.original_length || 0,
										r.message.cleaned_length || 0,
									]
								),
								indicator: "green",
							});

							frm.reload_doc();
						},
					});
				}
			);
		}, __("Text Processing"));

		frm.add_custom_button(__("Extract Provisions"), () => {
			extract_provisions(frm, 0);
		}, __("Text Processing"));

		frm.add_custom_button(__("Replace Extracted Provisions"), () => {
			frappe.confirm(
				__("Delete existing Legal Provision records for this expression and extract them again?"),
				() => extract_provisions(frm, 1)
			);
		}, __("Text Processing"));
	}
}

function extract_provisions(frm, replace_existing) {
	frappe.call({
		method: "za_legal_practice.legal_publishing.doctype.legal_instrument_expression.legal_instrument_expression.extract_provisions",
		args: {
			expression: frm.doc.name,
			replace_existing: replace_existing ? 1 : 0,
		},
		freeze: true,
		freeze_message: __("Extracting provisions..."),
		callback(r) {
			if (!r.message) {
				return;
			}

			frappe.show_alert({
				message: __("Created {0} provision(s).", [r.message.created_count || 0]),
				indicator: "green",
			});

			frm.reload_doc();
		},
	});
}

function get_akn_language_code(language) {
	const code = (language || "").trim().toLowerCase();

	const language_map = {
		en: "eng",
		eng: "eng",
		english: "eng",
		af: "afr",
		afr: "afr",
		afrikaans: "afr",
		zu: "zul",
		zul: "zul",
		zulu: "zul",
		xh: "xho",
		xho: "xho",
		xhosa: "xho",
		st: "sot",
		sot: "sot",
		tn: "tsn",
		tsn: "tsn",
		nso: "nso",
		ss: "ssw",
		ssw: "ssw",
		ve: "ven",
		ven: "ven",
		ts: "tso",
		tso: "tso",
		nr: "nbl",
		nbl: "nbl",
	};

	return language_map[code] || code;
}