# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class LegalForum(Document):
    """Legal Forum master for ZA Legal Practice.

    Represents courts, tribunals, commissions, arbitration forums,
    mediation forums, bargaining councils, and other legal fora.
    """

    def validate(self):
        self.normalize_forum_code()
        self.apply_forum_type_defaults()
        self.validate_forum_code()
        self.validate_default_party_role()
        self.validate_default_matter_stage()
        self.validate_practice_area()
        self.validate_matter_type()
        self.validate_default_uniqueness()
        self.validate_status()

    def normalize_forum_code(self):
        if not self.forum_code and self.forum_name:
            self.forum_code = make_code(self.forum_name)

        if self.forum_code:
            self.forum_code = make_code(self.forum_code)

    def apply_forum_type_defaults(self):
        forum_type = self.forum_type

        if forum_type == "Constitutional Court":
            self.forum_level = "Apex Court"
            self.jurisdiction_level = "National"
            self.appears_on_court_documents = 1
            self.default_party_role = self.default_party_role or "COURT"

        elif forum_type == "Supreme Court of Appeal":
            self.forum_level = "Appeal Court"
            self.jurisdiction_level = "National"
            self.appears_on_court_documents = 1
            self.default_party_role = self.default_party_role or "COURT"

        elif forum_type == "High Court":
            self.forum_level = "Superior Court"
            self.appears_on_court_documents = 1
            self.default_party_role = self.default_party_role or "COURT"

        elif forum_type in {"Labour Appeal Court", "Competition Appeal Court"}:
            self.forum_level = "Appeal Court"
            self.jurisdiction_level = "National"
            self.appears_on_court_documents = 1
            self.default_party_role = self.default_party_role or "COURT"

        elif forum_type in {
            "Labour Court",
            "Land Court",
            "Land Claims Court",
            "Electoral Court",
            "Tax Court",
            "Equality Court",
            "Small Claims Court",
            "Maintenance Court",
            "Children's Court",
            "Divorce Court",
        }:
            self.forum_level = "Specialist Court"
            self.appears_on_court_documents = 1
            self.default_party_role = self.default_party_role or "COURT"

        elif forum_type in {"Regional Magistrates Court", "District Magistrates Court"}:
            self.forum_level = "Lower Court"
            self.appears_on_court_documents = 1
            self.default_party_role = self.default_party_role or "COURT"

        elif forum_type in {
            "CCMA",
            "Bargaining Council",
            "Competition Tribunal",
            "Consumer Tribunal",
            "Companies Tribunal",
            "Tribunal",
        }:
            self.forum_level = "Commission / Tribunal"
            self.default_party_role = self.default_party_role or "COURT"

        elif forum_type in {"Arbitration Forum", "Mediation Forum"}:
            self.forum_level = "Forum"

    def validate_forum_code(self):
        if not self.forum_code:
            frappe.throw(_("Forum Code is required."))

        if not re.match(r"^[A-Z0-9_]+$", self.forum_code):
            frappe.throw(_("Forum Code may only contain uppercase letters, numbers, and underscores."))

        duplicate = frappe.db.exists(
            "Legal Forum",
            {
                "forum_code": self.forum_code,
                "name": ["!=", self.name],
            },
        )

        if duplicate:
            frappe.throw(
                _("Forum Code {0} is already used by Legal Forum {1}.").format(
                    frappe.bold(self.forum_code),
                    frappe.bold(duplicate),
                )
            )

    def validate_default_party_role(self):
        if not self.default_party_role:
            return

        role = frappe.db.get_value(
            "Legal Party Role",
            self.default_party_role,
            ["status", "disabled", "can_be_court_or_forum", "can_be_state_entity"],
            as_dict=True,
        )

        if not role:
            frappe.throw(_("Default Party Role {0} does not exist.").format(frappe.bold(self.default_party_role)))

        if role.status != "Active" or cint(role.disabled):
            frappe.throw(_("Default Party Role must be active."))

        if not cint(role.can_be_court_or_forum) and not cint(role.can_be_state_entity):
            frappe.throw(_("Default Party Role should be allowed as Court / Forum or State Entity."))

    def validate_default_matter_stage(self):
        if not self.default_matter_stage:
            return

        stage = frappe.db.get_value(
            "Matter Stage",
            self.default_matter_stage,
            ["status", "disabled"],
            as_dict=True,
        )

        if not stage:
            frappe.throw(_("Default Matter Stage {0} does not exist.").format(frappe.bold(self.default_matter_stage)))

        if stage.status != "Active" or cint(stage.disabled):
            frappe.throw(_("Default Matter Stage must be active."))

    def validate_practice_area(self):
        if not self.practice_area:
            return

        area = frappe.db.get_value(
            "Practice Area",
            self.practice_area,
            ["status", "disabled", "is_group"],
            as_dict=True,
        )

        if not area:
            frappe.throw(_("Practice Area {0} does not exist.").format(frappe.bold(self.practice_area)))

        if area.status != "Active" or cint(area.disabled):
            frappe.throw(_("Practice Area must be active."))

        if cint(area.is_group):
            frappe.throw(_("Practice Area must be a leaf Practice Area, not a group."))

    def validate_matter_type(self):
        if cint(self.applies_to_all_matter_types):
            self.matter_type = None
            return

        if not self.matter_type:
            frappe.throw(_("Matter Type is required unless Applies to All Matter Types is checked."))

        matter_type = frappe.db.get_value(
            "Matter Type",
            self.matter_type,
            ["status", "disabled", "practice_area"],
            as_dict=True,
        )

        if not matter_type:
            frappe.throw(_("Matter Type {0} does not exist.").format(frappe.bold(self.matter_type)))

        if matter_type.status != "Active" or cint(matter_type.disabled):
            frappe.throw(_("Matter Type must be active."))

        if self.practice_area and matter_type.practice_area and matter_type.practice_area != self.practice_area:
            frappe.throw(
                _("Matter Type {0} belongs to Practice Area {1}, not {2}.").format(
                    frappe.bold(self.matter_type),
                    frappe.bold(matter_type.practice_area),
                    frappe.bold(self.practice_area),
                )
            )

        if not self.practice_area and matter_type.practice_area:
            self.practice_area = matter_type.practice_area

    def validate_default_uniqueness(self):
        if not cint(self.is_default_for_type):
            return

        filters = self.get_scope_filters()
        filters.update(
            {
                "forum_type": self.forum_type,
                "is_default_for_type": 1,
                "disabled": 0,
                "name": ["!=", self.name],
            }
        )

        existing = frappe.db.exists("Legal Forum", filters)

        if existing:
            frappe.throw(
                _("Legal Forum {0} is already the default for this Forum Type and scope.").format(
                    frappe.bold(existing)
                )
            )

    def get_scope_filters(self):
        filters = {}

        if self.practice_area:
            filters["practice_area"] = self.practice_area
        else:
            filters["practice_area"] = ["in", ["", None]]

        if self.matter_type:
            filters["matter_type"] = self.matter_type
            filters["applies_to_all_matter_types"] = 0
        else:
            filters["matter_type"] = ["in", ["", None]]
            filters["applies_to_all_matter_types"] = 1

        return filters

    def validate_status(self):
        if cint(self.disabled) and self.status == "Active":
            self.status = "Inactive"

        if self.status == "Archived":
            self.disabled = 1


def make_code(value):
    value = (value or "").strip().upper()
    value = re.sub(r"[^A-Z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value)
    return value.strip("_")