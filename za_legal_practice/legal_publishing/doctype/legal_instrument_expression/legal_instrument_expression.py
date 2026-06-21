# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

import hashlib
import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime


class LegalInstrumentExpression(Document):
	"""Expression-level Akoma Ntoso document.

	A Legal Instrument Expression represents a specific language/date version of
	a Legal Instrument.

	Example:
		Legal Instrument:
			/akn/za/act/2013/4

		Expression:
			/akn/za/act/2013/4/eng@2013-11-26
	"""

	def autoname(self):
		self.normalize_values()
		self.validate_required_frbr_parts()
		self.set_frbr_expression_uri()
		self.name = make_document_name_from_frbr_expression_uri(self.frbr_expression_uri)

	def validate(self):
		self.normalize_values()
		self.validate_required_frbr_parts()
		self.set_expression_title()
		self.set_frbr_expression_uri()
		self.set_xml_hash()
		self.validate_frbr_expression_uri()

	def normalize_values(self):
		if self.version_label:
			self.version_label = self.version_label.strip()

		if self.expression_title:
			self.expression_title = self.expression_title.strip()

	def validate_required_frbr_parts(self):
		missing = []

		if not self.legal_instrument:
			missing.append(_("Legal Instrument"))

		if not self.language:
			missing.append(_("Language"))

		if not self.expression_date:
			missing.append(_("Expression Date"))

		if missing:
			frappe.throw(
				_("The following fields are required to generate the FRBR Expression URI: {0}.").format(
					", ".join(missing)
				)
			)

		instrument_frbr_uri = get_instrument_frbr_work_uri(self.legal_instrument)
		if not instrument_frbr_uri:
			frappe.throw(
				_("Legal Instrument {0} does not have a FRBR Work URI.").format(
					frappe.bold(self.legal_instrument)
				)
			)

	def set_expression_title(self):
		if self.expression_title:
			return

		instrument_title = frappe.db.get_value(
			"Legal Instrument",
			self.legal_instrument,
			"instrument_title",
		)

		language_code = get_akn_language_code(self.language)
		expression_date = getdate(self.expression_date).isoformat()

		if self.version_label:
			self.expression_title = f"{instrument_title} - {language_code} - {self.version_label}"
		else:
			self.expression_title = f"{instrument_title} - {language_code} - {expression_date}"

	def set_frbr_expression_uri(self):
		instrument_frbr_uri = get_instrument_frbr_work_uri(self.legal_instrument)
		language_code = get_akn_language_code(self.language)
		expression_date = getdate(self.expression_date).isoformat()

		self.frbr_expression_uri = make_frbr_expression_uri(
			instrument_frbr_uri=instrument_frbr_uri,
			language_code=language_code,
			expression_date=expression_date,
		)

	def set_xml_hash(self):
		if self.akn_xml:
			self.xml_hash = hashlib.sha256(self.akn_xml.encode("utf-8")).hexdigest()
		else:
			self.xml_hash = None

	def validate_frbr_expression_uri(self):
		if not self.frbr_expression_uri:
			frappe.throw(_("FRBR Expression URI is required."))

		if not self.frbr_expression_uri.startswith("/akn/"):
			frappe.throw(_("FRBR Expression URI must start with /akn/."))

		if "@" not in self.frbr_expression_uri:
			frappe.throw(_("FRBR Expression URI must include an expression date using @YYYY-MM-DD."))

		if not re.match(r"^/akn/[a-z0-9_/-]+/[a-z]{3}@[0-9]{4}-[0-9]{2}-[0-9]{2}$", self.frbr_expression_uri):
			frappe.throw(
				_(
					"FRBR Expression URI must follow the format "
					"/akn/{jurisdiction}/{doctype}/{year}/{number}/{language}@YYYY-MM-DD."
				)
			)

	def mark_published(self):
		self.published = 1
		self.expression_status = "Published"
		self.published_on = now_datetime()
		self.published_by = frappe.session.user


@frappe.whitelist()
def clean_ocr_text(expression: str, replace_existing: int = 1) -> dict:
	doc = frappe.get_doc("Legal Instrument Expression", expression)
	doc.check_permission("write")

	if not doc.bluebell_text:
		frappe.throw(_("Bluebell Text is empty. Copy OCR text to the expression first."))

	original_text = doc.bluebell_text
	cleaned_text = clean_legal_ocr_text(original_text)

	if not cleaned_text:
		frappe.throw(_("No usable text remained after cleaning."))

	if not int(replace_existing):
		return {
			"expression": doc.name,
			"original_length": len(original_text or ""),
			"cleaned_length": len(cleaned_text or ""),
			"cleaned_text": cleaned_text,
		}

	doc.bluebell_text = cleaned_text

	if doc.expression_status in ("Draft", "Imported"):
		doc.expression_status = "Parsed"

	doc.save(ignore_permissions=True)

	return {
		"expression": doc.name,
		"original_length": len(original_text or ""),
		"cleaned_length": len(cleaned_text or ""),
		"removed_length": len(original_text or "") - len(cleaned_text or ""),
	}


@frappe.whitelist()
def extract_provisions(expression: str, replace_existing: int = 0) -> dict:
	doc = frappe.get_doc("Legal Instrument Expression", expression)
	doc.check_permission("write")

	if not doc.bluebell_text:
		frappe.throw(_("Bluebell Text is empty. Clean or import text before extracting provisions."))

	if not frappe.db.exists("DocType", "Legal Provision"):
		frappe.throw(_("Legal Provision DocType does not exist."))

	if int(replace_existing):
		delete_existing_provisions(doc.name)
	else:
		existing_count = frappe.db.count("Legal Provision", {"expression": doc.name})
		if existing_count:
			frappe.throw(
				_("This expression already has {0} Legal Provision record(s). Use Replace Existing to regenerate.").format(
					existing_count
				)
			)

	body_text = get_legislative_body_text(doc.bluebell_text)
	provisions = parse_section_provisions(body_text)

	if not provisions:
		frappe.throw(_("No section provisions could be detected."))

	created = []

	for index, provision in enumerate(provisions, start=1):
		created.append(
			create_legal_provision(
				expression_doc=doc,
				provision=provision,
				sequence_no=index,
			)
		)

	if doc.expression_status in ("Draft", "Imported", "Parsed"):
		doc.expression_status = "Reviewed"
		doc.save(ignore_permissions=True)

	return {
		"expression": doc.name,
		"created_count": len(created),
		"first_provision": created[0] if created else None,
		"last_provision": created[-1] if created else None,
	}


def clean_legal_ocr_text(text: str) -> str:
	text = normalize_newlines(text)
	text = remove_ocr_skip_messages(text)
	text = remove_form_feed_markers(text)
	text = fix_common_ocr_spacing(text)
	text = normalize_broken_enacting_formula(text)
	text = remove_repeated_gazette_headers(text)
	text = remove_repeated_act_headers(text)
	text = remove_standalone_page_numbers(text)
	text = join_hyphenated_line_breaks(text)
	text = normalize_whitespace(text)
	text = trim_to_act_body_when_possible(text)
	text = remove_remaining_page_header_fragments(text)
	text = normalize_section_spacing(text)

	return text.strip()


def normalize_newlines(text: str) -> str:
	return text.replace("\r\n", "\n").replace("\r", "\n")


def remove_ocr_skip_messages(text: str) -> str:
	return re.sub(r"\[OCR skipped on page\(s\)[^\]]+\]\s*", "", text, flags=re.IGNORECASE)


def remove_form_feed_markers(text: str) -> str:
	return text.replace("\f", "\n")


def fix_common_ocr_spacing(text: str) -> str:
	replacements = {
		"t o ­": "to ",
		"t o-": "to ",
		"la)": "(a)",
		"fb)": "(b)",
		"fa)": "(a)",
		"{a)": "(a)",
		"gj": "(g)",
		"(\n)": "()",
		"—•": "—",
		"￾": "",
		"ﬁ": "fi",
		"ﬂ": "fl",
		"–": "-",
		"—": "-",
		"m u s t": "must",
		"A c t": "Act",
		"A c t -": "Act -",
		"n a s n e e n": "has been",
		"n\na\ns\nn\ne\ne\nn": "has been",
	}

	for old, new in replacements.items():
		text = text.replace(old, new)

	return text


def normalize_broken_enacting_formula(text: str) -> str:
	text = re.sub(
		r"\bB\s*\n\s*E IT ENACTED\b",
		"BE IT ENACTED",
		text,
		flags=re.IGNORECASE,
	)
	return text


def remove_repeated_gazette_headers(text: str) -> str:
	lines = []

	for line in text.split("\n"):
		clean = line.strip()

		if not clean:
			lines.append(line)
			continue

		if re.match(r"^\d+\s+No\.\s+\d+\s+GOVERNMENT GAZETTE,?\s+\d+\s+[A-Z]+\s+\d{4}$", clean, re.IGNORECASE):
			continue

		if re.match(r"^No\.\s+\d+\s+GOVERNMENT GAZETTE,?\s+\d+\s+[A-Z]+\s+\d{4}$", clean, re.IGNORECASE):
			continue

		if re.match(r"^GOVERNMENT GAZETTE,?\s+\d+\s+[A-Z]+\s+\d{4}$", clean, re.IGNORECASE):
			continue

		if re.match(r"^Vol\.\s+\d+\s+Cape Town\s+\d+\s+[A-Z]+\s+\d{4}\s+No\.\s+\d+$", clean, re.IGNORECASE):
			continue

		if clean.upper() in {"REPUBLIC OF SOUTH AFRICA", "GOVERNMENT GAZETTE"}:
			continue

		lines.append(line)

	return "\n".join(lines)


def remove_repeated_act_headers(text: str) -> str:
	lines = []

	for line in text.split("\n"):
		clean = line.strip()

		if not clean:
			lines.append(line)
			continue

		if re.match(r"^Act No\.\s+\d+,?\s+\d{4}\s+.+$", clean, re.IGNORECASE):
			continue

		if re.match(r"^.+ACT,\s+\d{4}$", clean, re.IGNORECASE) and len(clean) < 120:
			continue

		lines.append(line)

	return "\n".join(lines)


def remove_standalone_page_numbers(text: str) -> str:
	lines = []

	for line in text.split("\n"):
		clean = line.strip()

		if re.match(r"^\d+$", clean):
			continue

		if re.match(r"^\d+\s+No\.\s+\d+$", clean, re.IGNORECASE):
			continue

		lines.append(line)

	return "\n".join(lines)


def remove_remaining_page_header_fragments(text: str) -> str:
	lines = []

	for line in text.split("\n"):
		clean = line.strip()

		if re.match(r"^No\.\s+\d+$", clean, re.IGNORECASE):
			continue

		if re.match(r"^Act No\.\s+\d+,?\s+\d{4}$", clean, re.IGNORECASE):
			continue

		lines.append(line)

	return "\n".join(lines)


def join_hyphenated_line_breaks(text: str) -> str:
	text = re.sub(r"([A-Za-z])-\s*\n\s*([a-z])", r"\1\2", text)
	return text


def normalize_whitespace(text: str) -> str:
	lines = []

	for line in text.split("\n"):
		line = re.sub(r"[ \t]+", " ", line).strip()
		lines.append(line)

	text = "\n".join(lines)
	text = re.sub(r"\n{3,}", "\n\n", text)

	return text


def trim_to_act_body_when_possible(text: str) -> str:
	lines = text.split("\n")

	start_index = None

	for index, line in enumerate(lines):
		if line.strip().upper() == "ACT":
			start_index = index
			break

	if start_index is None:
		for index, line in enumerate(lines):
			if re.match(r"^To provide\b", line.strip(), re.IGNORECASE):
				start_index = index
				break

	if start_index is None:
		return text

	return "\n".join(lines[start_index:]).strip()


def normalize_section_spacing(text: str) -> str:
	text = re.sub(r"\n(?=(\d{1,3})\.\s+[A-Z])", "\n\n", text)
	text = re.sub(r"\n(?=CHAPTER\s+\d+)", "\n\n", text, flags=re.IGNORECASE)
	text = re.sub(r"\n(?=SCHEDULE\b)", "\n\n", text, flags=re.IGNORECASE)
	text = re.sub(r"\n{3,}", "\n\n", text)

	return text


def get_legislative_body_text(text: str) -> str:
	"""Return the part of the text that contains actual provisions.

	This avoids extracting the table of contents as if it were the Act body.
	For this Gazette format, the real body starts at SCHEDULE, followed by
	CHAPTER 1 / GENERAL PROVISIONS / Definitions / 1. (1).
	"""

	patterns = [
		r"\nSCHEDULE\s*\n\s*CHAPTER\s+1\s*\n\s*GENERAL PROVISIONS\s*\n\s*Definitions\s*\n\s*1\.\s*\(1\)",
		r"\nDefinitions\s*\n\s*1\.\s*\(1\)\s+In this Act",
		r"\n1\.\s*\(1\)\s+In this Act",
	]

	for pattern in patterns:
		match = re.search(pattern, text, flags=re.IGNORECASE)
		if match:
			start = match.start()
			body = text[start:].strip()

			if not body.upper().startswith("SCHEDULE") and "1. (1)" in body[:200]:
				body = "Definitions\n" + body

			return body

	return text


def parse_section_provisions(text: str) -> list[dict]:
	"""Extract numbered section provisions from cleaned legislative text.

	This is intentionally conservative. It extracts sections like:
	1. (1) In this Act...
	2. The purpose of this Act is...
	...
	96. (1) This Act is called...
	"""

	text = normalize_section_starts(text)

	section_start_pattern = re.compile(
		r"(?m)^(?P<number>\d{1,3})\.\s+(?P<first_line>.+)$"
	)

	matches = list(section_start_pattern.finditer(text))
	provisions = []

	for index, match in enumerate(matches):
		number = match.group("number")

		if not is_probable_section_number(number):
			continue

		start = match.start()
		end = matches[index + 1].start() if index + 1 < len(matches) else len(text)

		block = text[start:end].strip()

		if not block:
			continue

		heading = find_heading_before_section(text, start)
		body = block

		provisions.append(
			{
				"number": number,
				"heading": heading or f"Section {number}",
				"body_text": body,
			}
		)

	return dedupe_provisions_by_number(provisions)


def normalize_section_starts(text: str) -> str:
	"""Normalize common OCR layout where section number is on its own line.

	Example:
	2.
	Purpose and scope of Act

	2. The purpose of this Act is-

	This function does not try to convert the contents table. The extractor first
	trims to the real body, so this mainly helps body sections.
	"""

	text = re.sub(
		r"(?m)^(\d{1,3})\.\s*\n(?=\(\d+\)|[A-Z])",
		r"\1. ",
		text,
	)

	return text


def is_probable_section_number(number: str) -> bool:
	try:
		value = int(number)
	except ValueError:
		return False

	return 1 <= value <= 999


def find_heading_before_section(text: str, section_start: int) -> str | None:
	before = text[:section_start].rstrip()
	lines = [line.strip() for line in before.split("\n") if line.strip()]

	if not lines:
		return None

	ignore_patterns = [
		r"^CHAPTER\s+\d+$",
		r"^PART\s+\d+$",
		r"^SCHEDULE$",
		r"^GENERAL PROVISIONS$",
		r"^TRANSITIONAL AND FINAL MATTERS$",
		r"^REGULATION OF ROAD-BASED PUBLIC TRANSPORT$",
	]

	for line in reversed(lines[-8:]):
		if any(re.match(pattern, line, flags=re.IGNORECASE) for pattern in ignore_patterns):
			continue

		if re.match(r"^\d{1,3}\.", line):
			continue

		if len(line) > 140:
			continue

		return line

	return None


def dedupe_provisions_by_number(provisions: list[dict]) -> list[dict]:
	seen = set()
	deduped = []

	for provision in provisions:
		number = provision["number"]

		if number in seen:
			continue

		seen.add(number)
		deduped.append(provision)

	return deduped


def create_legal_provision(expression_doc: Document, provision: dict, sequence_no: int) -> str:
	provision_doc = frappe.new_doc("Legal Provision")

	provision_doc.legal_instrument = expression_doc.legal_instrument
	provision_doc.expression = expression_doc.name
	provision_doc.provision_type = "section"
	provision_doc.num = provision["number"]
	provision_doc.heading = provision["heading"]
	provision_doc.sequence_no = sequence_no
	provision_doc.text_content = provision["body_text"]

	provision_uri = make_section_provision_uri(expression_doc.legal_instrument, provision["number"])
	provision_doc.frbr_uri = provision_uri
	provision_doc.provision_path = f"/section/{provision['number']}"
	provision_doc.e_id = f"sec_{provision['number']}"

	provision_doc.insert(ignore_permissions=True)

	return provision_doc.name


def set_if_field(doc: Document, fieldname: str, value):
	if doc.meta.has_field(fieldname):
		doc.set(fieldname, value)


def delete_existing_provisions(expression_name: str):
	existing = frappe.get_all(
		"Legal Provision",
		filters={"expression": expression_name},
		pluck="name",
	)

	if not existing:
		existing = frappe.get_all(
			"Legal Provision",
			filters={"legal_instrument_expression": expression_name},
			pluck="name",
		)

	for name in existing:
		frappe.delete_doc("Legal Provision", name, ignore_permissions=True)


def make_section_provision_uri(legal_instrument: str, provision_number: str) -> str:
	frbr_work_uri = get_instrument_frbr_work_uri(legal_instrument)

	if not frbr_work_uri:
		return f"section/{provision_number}"

	return f"{frbr_work_uri.rstrip()}/section/{provision_number}"


def get_instrument_frbr_work_uri(legal_instrument: str) -> str:
	return frappe.db.get_value("Legal Instrument", legal_instrument, "frbr_work_uri")


def make_frbr_expression_uri(
	instrument_frbr_uri: str,
	language_code: str,
	expression_date: str,
) -> str:
	instrument_frbr_uri = instrument_frbr_uri.rstrip("/")
	language_code = language_code.strip().lower()
	expression_date = str(expression_date).strip()

	return f"{instrument_frbr_uri}/{language_code}@{expression_date}"


def make_document_name_from_frbr_expression_uri(frbr_expression_uri: str) -> str:
	return (
		frbr_expression_uri.strip("/")
		.replace("/", "-")
		.replace("@", "-")
	)


def get_akn_language_code(language: str) -> str:
	"""Return the ISO 639-2/T style language code used in AKN expression URIs."""

	if not language:
		frappe.throw(_("Language is required."))

	language = language.strip().lower()

	language_map = {
		"en": "eng",
		"eng": "eng",
		"english": "eng",
		"af": "afr",
		"afr": "afr",
		"afrikaans": "afr",
		"zu": "zul",
		"zul": "zul",
		"zulu": "zul",
		"xh": "xho",
		"xho": "xho",
		"xhosa": "xho",
		"st": "sot",
		"sot": "sot",
		"tn": "tsn",
		"tsn": "tsn",
		"nso": "nso",
		"ss": "ssw",
		"ssw": "ssw",
		"ve": "ven",
		"ven": "ven",
		"ts": "tso",
		"tso": "tso",
		"nr": "nbl",
		"nbl": "nbl",
	}

	if language in language_map:
		return language_map[language]

	if re.match(r"^[a-z]{3}$", language):
		return language

	frappe.throw(
		_("Language {0} cannot be converted to an AKN language code.").format(
			frappe.bold(language)
		)
	)