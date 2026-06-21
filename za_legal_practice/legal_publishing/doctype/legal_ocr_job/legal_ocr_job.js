// Copyright (c) 2026, BuFf0k and contributors
// For license information, please see license.txt

frappe.ui.form.on("Legal OCR Job", {
	refresh(frm) {
		add_custom_buttons(frm);
	},
});

function add_custom_buttons(frm) {
	if (frm.is_new()) {
		return;
	}

	if (frm.doc.source_manifestation) {
		frm.add_custom_button(__("Open Source Manifestation"), () => {
			frappe.set_route("Form", "Legal Instrument Manifestation", frm.doc.source_manifestation);
		}, __("Legal Publishing"));
	}

	if (frm.doc.source_manifestation && ["Queued", "Failed", "Cancelled"].includes(frm.doc.status)) {
		frm.add_custom_button(__("Run OCR"), () => {
			frappe.confirm(
				__("Run OCR now? This may take a while for large PDFs."),
				() => {
					frappe.call({
						method: "za_legal_practice.legal_publishing.doctype.legal_ocr_job.legal_ocr_job.run_ocr",
						args: {
							ocr_job: frm.doc.name,
						},
						freeze: true,
						freeze_message: __("Running OCR..."),
						callback(r) {
							if (r.message) {
								frappe.show_alert({
									message: __("OCR completed. Text length: {0}", [r.message.text_length || 0]),
									indicator: "green",
								});
							}

							frm.reload_doc();
						},
					});
				}
			);
		}, __("OCR"));
	}

	if (frm.doc.output_pdf) {
		frm.add_custom_button(__("Open OCR PDF"), () => {
			window.open(frm.doc.output_pdf, "_blank");
		}, __("OCR"));
	}

	if (frm.doc.output_text && frm.doc.status === "Completed") {
		frm.add_custom_button(__("Copy Text to Expression"), () => {
			frappe.confirm(
				__("Copy OCR Output Text to the linked Expression's Bluebell Text field?"),
				() => copy_ocr_text_to_expression(frm, 0)
			);
		}, __("OCR"));

		frm.add_custom_button(__("Replace Expression Text"), () => {
			frappe.confirm(
				__("Replace the linked Expression's existing Bluebell Text with this OCR Output Text?"),
				() => copy_ocr_text_to_expression(frm, 1)
			);
		}, __("OCR"));
	}
}

function copy_ocr_text_to_expression(frm, replace_existing) {
	frappe.call({
		method: "za_legal_practice.legal_publishing.doctype.legal_ocr_job.legal_ocr_job.copy_ocr_text_to_expression",
		args: {
			ocr_job: frm.doc.name,
			replace_existing: replace_existing ? 1 : 0,
		},
		freeze: true,
		freeze_message: __("Copying OCR text..."),
		callback(r) {
			if (!r.message) {
				return;
			}

			frappe.show_alert({
				message: __("Copied OCR text to Expression {0}", [r.message]),
				indicator: "green",
			});

			frappe.set_route("Form", "Legal Instrument Expression", r.message);
		},
	});
}