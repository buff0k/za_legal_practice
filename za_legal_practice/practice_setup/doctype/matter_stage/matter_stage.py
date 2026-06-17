# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class MatterStage(Document):
    """Matter Stage master for ZA Legal Practice.

    Matter Stage represents the operational progress of a matter.
    It is intentionally separate from workflow status.

    Example:
        status = Active
        stage = Discovery

    Workflow status controls the system state.
    Matter stage controls legal-operational progress.
    """

    def validate(self):
        self.normalize_stage_code()
        self.validate_stage_code()
        self.validate_practice_area()
        self.validate_matter_type()
        self.validate_stage_links()
        self.validate_role_links()
        self.validate_stage_flags()
        self.validate_stage_uniqueness()
        self.validate_status()

    def normalize_stage_code(self):
        if not self.stage_code and self.stage_name:
            self.stage_code = make_code(self.stage_name)

        if self.stage_code:
            self.stage_code = make_code(self.stage_code)

    def validate_stage_code(self):
        if not self.stage_code:
            frappe.throw(_("Stage Code is required."))

        if not re.match(r"^[A-Z0-9_]+$", self.stage_code):
            frappe.throw(_("Stage Code may only contain uppercase letters, numbers, and underscores."))

        duplicate = frappe.db.exists(
            "Matter Stage",
            {
                "stage_code": self.stage_code,
                "name": ["!=", self.name],
            },
        )

        if duplicate:
            frappe.throw(
                _("Stage Code {0} is already used by Matter Stage {1}.").format(
                    frappe.bold(self.stage_code),
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

    def validate_stage_links(self):
        for fieldname, label in {
            "next_stage": _("Next Stage"),
            "previous_stage": _("Previous Stage"),
        }.items():
            stage = self.get(fieldname)

            if not stage:
                continue

            if stage == self.name:
                frappe.throw(_("{0} cannot refer to this same Matter Stage.").format(label))

            if not frappe.db.exists("Matter Stage", stage):
                frappe.throw(_("{0} {1} does not exist.").format(label, frappe.bold(stage)))

            linked_stage = frappe.db.get_value(
                "Matter Stage",
                stage,
                ["status", "disabled", "practice_area", "matter_type", "applies_to_all_matter_types"],
                as_dict=True,
            )

            if linked_stage.status != "Active" or cint(linked_stage.disabled):
                frappe.throw(_("{0} must be active.").format(label))

            if self.practice_area and linked_stage.practice_area and linked_stage.practice_area != self.practice_area:
                frappe.throw(
                    _("{0} belongs to Practice Area {1}, not {2}.").format(
                        label,
                        frappe.bold(linked_stage.practice_area),
                        frappe.bold(self.practice_area),
                    )
                )

            if (
                self.matter_type
                and linked_stage.matter_type
                and linked_stage.matter_type != self.matter_type
                and not cint(linked_stage.applies_to_all_matter_types)
            ):
                frappe.throw(
                    _("{0} belongs to Matter Type {1}, not {2}.").format(
                        label,
                        frappe.bold(linked_stage.matter_type),
                        frappe.bold(self.matter_type),
                    )
                )

    def validate_role_links(self):
        for fieldname, label in {
            "approval_role": _("Approval Role"),
            "escalation_role": _("Escalation Role"),
        }.items():
            role = self.get(fieldname)

            if role and not frappe.db.exists("Role", role):
                frappe.throw(_("{0} {1} does not exist.").format(label, frappe.bold(role)))

        if cint(self.require_partner_approval) and not self.approval_role:
            frappe.throw(_("Approval Role is required when Require Partner Approval is checked."))

    def validate_stage_flags(self):
        if cint(self.is_closed_stage):
            self.is_closing_stage = 1
            self.allow_trust_receipts = 0
            self.allow_trust_payments = 0
            self.allow_trust_to_business_transfers = 0
            self.allow_time_entries = 0
            self.allow_disbursements = 0
            self.allow_billing = 0
            self.prevent_trust_activity = 1
            self.require_trust_balance_zero = 1
            self.require_unbilled_time_clear = 1
            self.require_unbilled_disbursements_clear = 1
            self.require_open_tasks_complete = 1

        if cint(self.prevent_trust_activity):
            self.allow_trust_receipts = 0
            self.allow_trust_payments = 0
            self.allow_trust_to_business_transfers = 0

        if cint(self.is_closing_stage):
            self.require_required_documents_complete = 1
            self.require_open_tasks_complete = 1

        if cint(self.is_initial_stage):
            self.is_default_stage = 1

        if cint(self.target_days) < 0:
            frappe.throw(_("Target Days cannot be negative."))

        if cint(self.warning_days_before_target) < 0:
            frappe.throw(_("Warning Days Before Target cannot be negative."))

        if cint(self.warning_days_before_target) and cint(self.target_days):
            if cint(self.warning_days_before_target) > cint(self.target_days):
                frappe.throw(_("Warning Days Before Target cannot be greater than Target Days."))

    def validate_stage_uniqueness(self):
        scope_filters = self.get_scope_filters()

        unique_flag_fields = {
            "is_initial_stage": _("initial stage"),
            "is_default_stage": _("default stage"),
            "is_closed_stage": _("closed stage"),
        }

        for fieldname, label in unique_flag_fields.items():
            if not cint(self.get(fieldname)):
                continue

            filters = dict(scope_filters)
            filters[fieldname] = 1
            filters["disabled"] = 0
            filters["name"] = ["!=", self.name]

            existing = frappe.db.exists("Matter Stage", filters)

            if existing:
                frappe.throw(
                    _("Matter Stage {0} is already marked as the {1} for this scope.").format(
                        frappe.bold(existing),
                        label,
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