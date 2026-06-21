# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import unquote

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime
from frappe.utils.file_manager import save_file


class LegalOCRJob(Document):
	"""OCR job record for source legal-publishing files."""

	def validate(self):
		self.validate_language_codes()

	def validate_language_codes(self):
		if not self.language_codes:
			self.language_codes = "eng"

		self.language_codes = self.language_codes.strip()

		if " " in self.language_codes:
			frappe.throw(_("Language Codes must use OCR engine syntax, for example eng or eng+afr."))


@frappe.whitelist()
def run_ocr(ocr_job: str) -> dict:
	doc = frappe.get_doc("Legal OCR Job", ocr_job)
	doc.check_permission("write")

	validate_ocr_environment()

	if not doc.source_manifestation:
		frappe.throw(_("Source Manifestation is required."))

	manifestation = frappe.get_doc("Legal Instrument Manifestation", doc.source_manifestation)

	if not manifestation.file:
		frappe.throw(
			_("Source Manifestation {0} does not have a file attached.").format(
				frappe.bold(manifestation.name)
			)
		)

	source_pdf_path = resolve_site_file_path(manifestation.file)

	if not source_pdf_path.exists():
		frappe.throw(_("Source file does not exist on disk: {0}").format(source_pdf_path))

	if source_pdf_path.suffix.lower() != ".pdf":
		frappe.throw(_("OCR currently supports PDF files only."))

	doc.db_set("status", "Running", update_modified=True)
	doc.db_set("started_on", now_datetime(), update_modified=True)
	doc.db_set("error_log", None, update_modified=True)

	try:
		with tempfile.TemporaryDirectory() as tmpdir:
			tmpdir_path = Path(tmpdir)
			output_pdf_path = tmpdir_path / build_output_pdf_name(source_pdf_path)
			sidecar_text_path = tmpdir_path / "ocr_output.txt"

			command = build_ocrmypdf_command(
				doc=doc,
				source_pdf_path=source_pdf_path,
				output_pdf_path=output_pdf_path,
				sidecar_text_path=sidecar_text_path,
			)

			completed = subprocess.run(
				command,
				check=False,
				capture_output=True,
				text=True,
			)

			if completed.returncode != 0:
				error_log = "\n".join(
					part
					for part in [
						"Command:",
						" ".join(command),
						"\nSTDOUT:",
						completed.stdout,
						"\nSTDERR:",
						completed.stderr,
					]
					if part
				)

				doc.db_set("status", "Failed", update_modified=True)
				doc.db_set("error_log", error_log, update_modified=True)

				frappe.throw(_("OCR failed. Check the OCR Job error log."))

			output_text = read_ocr_text(output_pdf_path, sidecar_text_path)

			if not output_text:
				doc.db_set("status", "Failed", update_modified=True)
				doc.db_set(
					"error_log",
					_("OCR completed, but no usable text could be extracted from the output PDF."),
					update_modified=True,
				)
				frappe.throw(_("OCR completed, but no usable text could be extracted."))

			file_doc = attach_output_pdf(
				output_pdf_path=output_pdf_path,
				ocr_job=doc.name,
			)

			doc.output_pdf = file_doc.file_url
			doc.output_text = output_text
			doc.output_json = json.dumps(
				{
					"source_manifestation": manifestation.name,
					"source_file": manifestation.file,
					"source_pdf_path": str(source_pdf_path),
					"output_file": file_doc.file_url,
					"engine": doc.ocr_engine,
					"language_codes": doc.language_codes,
					"command": command,
					"text_length": len(output_text or ""),
				},
				indent=2,
			)
			doc.status = "Completed"
			doc.completed_on = now_datetime()
			doc.save(ignore_permissions=True)

			create_ocr_manifestation_if_possible(
				source_manifestation=manifestation,
				output_file_url=file_doc.file_url,
				ocr_job=doc,
			)

			return {
				"status": "Completed",
				"ocr_job": doc.name,
				"output_pdf": file_doc.file_url,
				"text_length": len(output_text or ""),
			}

	except Exception as exc:
		if frappe.db.exists("Legal OCR Job", doc.name):
			frappe.db.set_value("Legal OCR Job", doc.name, "status", "Failed")
			frappe.db.set_value("Legal OCR Job", doc.name, "error_log", frappe.get_traceback())

		raise exc


@frappe.whitelist()
def copy_ocr_text_to_expression(ocr_job: str, replace_existing: int = 0) -> str:
	doc = frappe.get_doc("Legal OCR Job", ocr_job)
	doc.check_permission("write")

	if not doc.output_text:
		frappe.throw(_("OCR Job does not have Output Text."))

	if not has_usable_text(doc.output_text):
		frappe.throw(_("OCR Job Output Text does not contain usable extracted text."))

	manifestation = frappe.get_doc("Legal Instrument Manifestation", doc.source_manifestation)

	if not manifestation.expression:
		frappe.throw(_("Source Manifestation is not linked to a Legal Instrument Expression."))

	expression = frappe.get_doc("Legal Instrument Expression", manifestation.expression)

	if expression.bluebell_text and not int(replace_existing):
		frappe.throw(_("Expression already has Bluebell Text. Use Replace Existing to overwrite it."))

	expression.bluebell_text = doc.output_text
	expression.expression_status = "Imported"
	expression.save(ignore_permissions=True)

	return expression.name


def validate_ocr_environment():
	missing = []

	if not is_python_module_available("ocrmypdf"):
		missing.append("ocrmypdf Python package")

	for executable in ["tesseract", "gs", "qpdf"]:
		if not shutil.which(executable):
			missing.append(executable)

	if missing:
		frappe.throw(
			_("Missing required OCR dependency/dependencies: {0}. Install Python and apt dependencies first.").format(
				", ".join(missing)
			)
		)


def is_python_module_available(module_name: str) -> bool:
	completed = subprocess.run(
		[sys.executable, "-m", module_name, "--version"],
		check=False,
		capture_output=True,
		text=True,
	)

	return completed.returncode == 0


def build_ocrmypdf_command(
	doc: Document,
	source_pdf_path: Path,
	output_pdf_path: Path,
	sidecar_text_path: Path,
) -> list[str]:
	command = [
		sys.executable,
		"-m",
		"ocrmypdf",
		"--language",
		doc.language_codes or "eng",
		"--rotate-pages",
		"--sidecar",
		str(sidecar_text_path),
	]

	if int(doc.deskew or 0):
		command.append("--deskew")

	if int(doc.clean or 0):
		command.append("--clean")

	if int(doc.force_ocr or 0):
		command.append("--force-ocr")
	else:
		command.append("--skip-text")

	command.extend(
		[
			str(source_pdf_path),
			str(output_pdf_path),
		]
	)

	return command


def read_ocr_text(output_pdf_path: Path, sidecar_text_path: Path) -> str:
	sidecar_text = ""

	if sidecar_text_path.exists():
		sidecar_text = sidecar_text_path.read_text(encoding="utf-8", errors="replace").strip()

	if has_usable_text(sidecar_text):
		return sidecar_text

	pdf_text = extract_text_from_pdf(output_pdf_path)

	if has_usable_text(pdf_text):
		return pdf_text

	return ""


def has_usable_text(text: str | None) -> bool:
	if not text:
		return False

	cleaned = text.strip()

	if not cleaned:
		return False

	# OCRmyPDF writes this when --skip-text skips every page.
	if re.fullmatch(r"(\[OCR skipped on page\(s\)[^\]]+\]\s*)+", cleaned):
		return False

	# Avoid accepting tiny status strings as legal text.
	if len(cleaned) < 100:
		return False

	return True


def extract_text_from_pdf(output_pdf_path: Path) -> str:
	try:
		import fitz

		text_parts = []

		with fitz.open(str(output_pdf_path)) as pdf:
			for page in pdf:
				page_text = page.get_text("text")
				if page_text:
					text_parts.append(page_text)

		return "\n".join(text_parts).strip()

	except Exception:
		return ""


def attach_output_pdf(output_pdf_path: Path, ocr_job: str):
	content = output_pdf_path.read_bytes()

	return save_file(
		fname=output_pdf_path.name,
		content=content,
		dt="Legal OCR Job",
		dn=ocr_job,
		is_private=1,
	)


def create_ocr_manifestation_if_possible(
	source_manifestation: Document,
	output_file_url: str,
	ocr_job: Document,
):
	if not source_manifestation.legal_instrument:
		return

	ocr_manifestation = frappe.new_doc("Legal Instrument Manifestation")
	ocr_manifestation.legal_instrument = source_manifestation.legal_instrument
	ocr_manifestation.expression = source_manifestation.expression
	ocr_manifestation.manifestation_type = "OCR PDF"
	ocr_manifestation.file = output_file_url
	ocr_manifestation.source_url = source_manifestation.source_url
	ocr_manifestation.is_searchable_pdf = 1
	ocr_manifestation.ocr_required = 0
	ocr_manifestation.ocr_job = ocr_job.name
	ocr_manifestation.imported_on = now_datetime()
	ocr_manifestation.imported_by = frappe.session.user
	ocr_manifestation.insert(ignore_permissions=True)


def build_output_pdf_name(source_pdf_path: Path) -> str:
	stem = source_pdf_path.stem.replace(" ", "_")
	return f"{stem}_ocr.pdf"


def resolve_site_file_path(file_url: str) -> Path:
	file_url = unquote(file_url or "")

	if not file_url:
		frappe.throw(_("File URL is required."))

	file_name = Path(file_url).name

	if file_url.startswith("/private/files/"):
		return Path(frappe.get_site_path("private", "files", file_name)).resolve()

	if file_url.startswith("/files/"):
		return Path(frappe.get_site_path("public", "files", file_name)).resolve()

	if file_url.startswith("private/files/"):
		return Path(frappe.get_site_path(file_url)).resolve()

	if file_url.startswith("files/"):
		return Path(frappe.get_site_path("public", file_url)).resolve()

	frappe.throw(_("Unsupported file URL format: {0}").format(file_url))