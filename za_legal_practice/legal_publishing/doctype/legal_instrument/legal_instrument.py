# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document


class LegalInstrument(Document):
	"""Legal publishing work-level instrument."""

	def autoname(self):
		self.normalize_values()
		self.validate_required_frbr_parts()
		self.set_frbr_work_uri()
		self.name = make_document_name_from_frbr_uri(self.frbr_work_uri)

	def validate(self):
		self.normalize_values()
		self.validate_required_frbr_parts()
		self.set_frbr_work_uri()
		self.validate_year()
		self.validate_number()
		self.validate_frbr_work_uri()

	def normalize_values(self):
		if self.jurisdiction:
			self.jurisdiction = self.jurisdiction.strip().lower()

		if self.akn_doctype:
			self.akn_doctype = self.akn_doctype.strip()

		if self.number:
			self.number = str(self.number).strip()

	def validate_required_frbr_parts(self):
		missing = []

		if not self.jurisdiction:
			missing.append(_("Jurisdiction"))

		if not self.akn_doctype:
			missing.append(_("AKN Document Type"))

		if not self.year:
			missing.append(_("Year"))

		if not self.number:
			missing.append(_("Number"))

		if missing:
			frappe.throw(
				_("The following fields are required to generate the FRBR Work URI: {0}.").format(
					", ".join(missing)
				)
			)

	def set_frbr_work_uri(self):
		self.frbr_work_uri = make_frbr_work_uri(
			jurisdiction=self.jurisdiction,
			akn_doctype=self.akn_doctype,
			year=self.year,
			number=self.number,
		)

	def validate_year(self):
		if self.year and (self.year < 1600 or self.year > 2200):
			frappe.throw(_("Year must be between 1600 and 2200."))

	def validate_number(self):
		if not self.number:
			frappe.throw(_("Number is required."))

		if "/" in self.number:
			frappe.throw(_("Number may not contain a slash."))

	def validate_frbr_work_uri(self):
		if not self.frbr_work_uri:
			frappe.throw(_("FRBR Work URI is required."))

		if not self.frbr_work_uri.startswith("/akn/"):
			frappe.throw(_("FRBR Work URI must start with /akn/."))

		if not re.match(r"^/akn/[a-z0-9_/-]+$", self.frbr_work_uri):
			frappe.throw(
				_("FRBR Work URI may only contain lowercase letters, numbers, underscores, dashes and slashes.")
			)


def make_frbr_work_uri(jurisdiction: str, akn_doctype: str, year: int | str, number: int | str) -> str:
	jurisdiction = str(jurisdiction).strip().lower()
	akn_doctype = str(akn_doctype).strip()
	year = str(year).strip()
	number = str(number).strip()

	return f"/akn/{jurisdiction}/{akn_doctype}/{year}/{number}"


def make_document_name_from_frbr_uri(frbr_work_uri: str) -> str:
	return frbr_work_uri.strip("/").replace("/", "-")