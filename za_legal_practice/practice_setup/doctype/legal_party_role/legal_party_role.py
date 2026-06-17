# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class LegalPartyRole(Document):
    """Legal Party Role master for ZA Legal Practice.

    Defines the role a party plays in a matter:
    - client side
    - opposing side
    - third party
    - professional party
    - court/forum/state entity
    - litigation, conveyancing, collections, estate, family, criminal, etc.
    """

    def validate(self):
        self.normalize_role_code()
        self.apply_category_defaults()
        self.validate_role_code()
        self.validate_practice_area()
        self.validate_matter_type()
        self.validate_roles_and_flags()
        self.validate_default_uniqueness()
        self.validate_status()

    def normalize_role_code(self):
        if not self.role_code and self.role_name:
            self.role_code = make_code(self.role_name)

        if self.role_code:
            self.role_code = make_code(self.role_code)

    def apply_category_defaults(self):
        category = self.role_category

        if category == "Client":
            self.can_be_client = 1
            self.can_be_opposing_party = 0
            self.can_be_third_party = 0
            self.party_side = "Client Side"
            self.include_in_conflict_check = 1
            self.include_in_fica_check = 1
            self.requires_fica = 1
            self.requires_mandate = 1
            self.requires_id_or_registration_number = 1
            self.requires_address = 1
            self.include_in_billing = 1

        elif category == "Opposing Party":
            self.can_be_client = 0
            self.can_be_opposing_party = 1
            self.can_be_third_party = 0
            self.party_side = "Opposing Side"
            self.include_in_conflict_check = 1
            self.include_in_fica_check = 0
            self.requires_mandate = 0

        elif category == "Professional":
            self.can_be_professional_party = 1
            self.can_be_third_party = 1
            self.party_side = "Third Party"
            self.requires_fica = 0
            self.requires_mandate = 0

        elif category == "Court / Forum":
            self.can_be_court_or_forum = 1
            self.can_be_third_party = 0
            self.party_side = "Court / Forum"
            self.include_in_conflict_check = 0
            self.include_in_fica_check = 0
            self.requires_fica = 0
            self.requires_mandate = 0
            self.requires_contact_details = 1

        elif category == "State Entity":
            self.can_be_state_entity = 1
            self.party_side = "Third Party"
            self.include_in_conflict_check = 1

        elif category == "Internal":
            self.can_be_internal_party = 1
            self.can_be_third_party = 0
            self.party_side = "Internal"
            self.include_in_conflict_check = 0
            self.include_in_fica_check = 0
            self.requires_fica = 0
            self.requires_mandate = 0

        elif category == "Litigation":
            self.include_in_conflict_check = 1
            self.include_in_documents = 1
            self.appears_on_court_documents = 1

        elif category == "Conveyancing":
            self.include_in_conflict_check = 1
            self.include_in_documents = 1
            self.requires_address = 1

        elif category == "Collections":
            self.include_in_conflict_check = 1
            self.include_in_documents = 1

        if cint(self.requires_fica):
            self.include_in_fica_check = 1
            self.requires_id_or_registration_number = 1
            self.requires_address = 1

        if cint(self.requires_mandate):
            self.can_be_client = 1
            self.party_side = "Client Side"

        if self.party_side == "Client Side":
            self.can_be_client = 1

        if self.party_side == "Opposing Side":
            self.can_be_opposing_party = 1

        if self.party_side == "Court / Forum":
            self.can_be_court_or_forum = 1

        if self.party_side == "Internal":
            self.can_be_internal_party = 1

    def validate_role_code(self):
        if not self.role_code:
            frappe.throw(_("Role Code is required."))

        if not re.match(r"^[A-Z0-9_]+$", self.role_code):
            frappe.throw(_("Role Code may only contain uppercase letters, numbers, and underscores."))

        duplicate = frappe.db.exists(
            "Legal Party Role",
            {
                "role_code": self.role_code,
                "name": ["!=", self.name],
            },
        )

        if duplicate:
            frappe.throw(
                _("Role Code {0} is already used by Legal Party Role {1}.").format(
                    frappe.bold(self.role_code),
                    frappe.bold(duplicate),
                )
            )

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

    def validate_roles_and_flags(self):
        if not any(
            [
                cint(self.can_be_client),
                cint(self.can_be_opposing_party),
                cint(self.can_be_third_party),
                cint(self.can_be_professional_party),
                cint(self.can_be_court_or_forum),
                cint(self.can_be_state_entity),
                cint(self.can_be_internal_party),
                cint(self.can_be_related_party),
            ]
        ):
            frappe.throw(_("At least one party behaviour flag must be enabled."))

        if cint(self.required_on_matter) and not self.allow_multiple_parties:
            # This is allowed, but intentionally explicit. A required role may occur once only.
            pass

        if cint(self.requires_mandate) and not cint(self.can_be_client):
            frappe.throw(_("A role that requires mandate must be allowed as a client role."))

        if cint(self.include_in_fica_check) and not cint(self.requires_fica):
            self.requires_fica = 1

        if cint(self.is_debtor_role):
            self.collections_role_type = self.collections_role_type or "Debtor"

        if cint(self.is_creditor_role):
            self.collections_role_type = self.collections_role_type or "Creditor"

        if cint(self.is_surety_role):
            self.collections_role_type = self.collections_role_type or "Surety"

        if cint(self.is_primary_litigation_party):
            self.role_category = "Litigation"
            self.appears_on_court_documents = 1
            self.include_in_documents = 1

        if cint(self.is_primary_conveyancing_party):
            self.role_category = "Conveyancing"
            self.include_in_documents = 1
            self.requires_address = 1

        if cint(self.can_be_court_or_forum):
            self.party_side = "Court / Forum"

        if cint(self.can_be_internal_party):
            self.party_side = "Internal"

    def validate_default_uniqueness(self):
        if not cint(self.is_default_for_category):
            return

        filters = self.get_scope_filters()
        filters.update(
            {
                "role_category": self.role_category,
                "party_side": self.party_side,
                "is_default_for_category": 1,
                "disabled": 0,
                "name": ["!=", self.name],
            }
        )

        existing = frappe.db.exists("Legal Party Role", filters)

        if existing:
            frappe.throw(
                _("Legal Party Role {0} is already the default for this category/side/scope.").format(
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