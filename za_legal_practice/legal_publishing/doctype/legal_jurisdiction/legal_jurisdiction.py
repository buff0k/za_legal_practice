# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document


class LegalJurisdiction(Document):
	"""Jurisdiction master for legal publishing."""

	def autoname(self):
		self.normalize_code()
		self.name = self.jurisdiction_code

	def validate(self):
		self.normalize_code()
		self.validate_code()
		self.validate_parent()

	def normalize_code(self):
		if self.jurisdiction_code:
			self.jurisdiction_code = self.jurisdiction_code.strip().lower().replace(" ", "-")

	def validate_code(self):
		if not self.jurisdiction_code:
			frappe.throw(_("Jurisdiction Code is required."))

		if not re.match(r"^[a-z0-9_-]+$", self.jurisdiction_code):
			frappe.throw(_("Jurisdiction Code may only contain lowercase letters, numbers, underscores and dashes."))

	def validate_parent(self):
		if self.parent_jurisdiction and self.parent_jurisdiction == self.name:
			frappe.throw(_("Parent Jurisdiction cannot be the same as this jurisdiction."))