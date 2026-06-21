# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class LegalEditorialNote(Document):
	"""Editorial note linked to a legal instrument, expression or provision."""

	def before_insert(self):
		if not self.created_by_user:
			self.created_by_user = frappe.session.user
