# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

import hashlib
from pathlib import Path
from urllib.parse import unquote

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class LegalInstrumentManifestation(Document):
	"""Manifestation-level source or generated file."""

	def before_insert(self):
		if not self.imported_on:
			self.imported_on = now_datetime()

		if not self.imported_by:
			self.imported_by = frappe.session.user

	def validate(self):
		self.validate_expression_belongs_to_instrument()
		self.set_file_metadata()

	def validate_expression_belongs_to_instrument(self):
		if not self.expression or not self.legal_instrument:
			return

		expression_instrument = frappe.db.get_value(
			"Legal Instrument Expression",
			self.expression,
			"legal_instrument",
		)

		if expression_instrument and expression_instrument != self.legal_instrument:
			frappe.throw(
				_("Expression {0} does not belong to Legal Instrument {1}.").format(
					frappe.bold(self.expression),
					frappe.bold(self.legal_instrument),
				)
			)

	def set_file_metadata(self):
		if not self.file:
			return

		path = resolve_site_file_path(self.file)

		if not path.exists():
			return

		self.file_hash = sha256_file(path)
		self.mime_type = guess_mime_type(path)

		if path.suffix.lower() == ".pdf":
			self.page_count = get_pdf_page_count(path)


@frappe.whitelist()
def create_ocr_job(source_manifestation: str) -> str:
	manifestation = frappe.get_doc("Legal Instrument Manifestation", source_manifestation)

	if not manifestation.file:
		frappe.throw(_("Attach a source file before creating an OCR Job."))

	if manifestation.ocr_job and frappe.db.exists("Legal OCR Job", manifestation.ocr_job):
		return manifestation.ocr_job

	job = frappe.new_doc("Legal OCR Job")
	job.source_manifestation = manifestation.name
	job.status = "Queued"
	job.ocr_engine = "OCRmyPDF/Tesseract"
	job.language_codes = "eng"
	job.deskew = 1
	job.clean = 1
	job.force_ocr = 0
	job.insert(ignore_permissions=True)

	manifestation.db_set("ocr_job", job.name, update_modified=True)

	return job.name


def resolve_site_file_path(file_url: str) -> Path:
	file_url = unquote(file_url or "")

	if not file_url:
		frappe.throw(_("File URL is required."))

	file_name = Path(file_url).name

	if file_url.startswith("/private/files/"):
		return Path(frappe.get_site_path("private", "files", file_name))

	if file_url.startswith("/files/"):
		return Path(frappe.get_site_path("public", "files", file_name))

	# Fallback for stored relative URLs.
	if file_url.startswith("private/files/"):
		return Path(frappe.get_site_path(file_url))

	if file_url.startswith("files/"):
		return Path(frappe.get_site_path("public", file_url))

	frappe.throw(_("Unsupported file URL format: {0}").format(file_url))


def sha256_file(path: Path) -> str:
	hash_obj = hashlib.sha256()

	with path.open("rb") as handle:
		for chunk in iter(lambda: handle.read(1024 * 1024), b""):
			hash_obj.update(chunk)

	return hash_obj.hexdigest()


def guess_mime_type(path: Path) -> str:
	try:
		import magic

		return magic.from_file(str(path), mime=True)
	except Exception:
		if path.suffix.lower() == ".pdf":
			return "application/pdf"

		return "application/octet-stream"


def get_pdf_page_count(path: Path) -> int | None:
	try:
		import fitz

		with fitz.open(str(path)) as pdf:
			return pdf.page_count
	except Exception:
		return None