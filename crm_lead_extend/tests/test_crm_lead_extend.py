###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class CrmLeadExtend(TransactionCase):

    def setUp(self):
        super().setUp()
        self.lead_obj = self.env['crm.lead']
        self.lead = self.lead_obj.create({
            'name': 'test lead',
            'budget': 1000
        })

    def test_10_field_budget(self):
        with self.assertRaises(ValueError, msg="The value must be number"):
            self.lead.budget = "test"

    def test_20_field_desicion_makers_ids(self):
        with self.assertRaises(ValueError, msg="The value must be many2many"):
            self.lead.decision_makers_ids = -1

    def test_30_field_quarter_decision(self):
        with self.assertRaises(ValueError, msg="The value must be number"):
            self.lead.quarter_decision = "test"

    def test_40_field_year_decision(self):
        with self.assertRaises(ValueError, msg="The value must be number"):
            self.lead.year_decision = "test"

    def test_50_field_quarter_implementation(self):
        with self.assertRaises(ValueError, msg="The value must be number"):
            self.lead.quarter_decision = "test"

    def test_60_field_year_implementation(self):
        with self.assertRaises(ValueError, msg="The value must be number"):
            self.lead.year_implementation = "test"

    def test_70_field_employes_number(self):
        with self.assertRaises(ValueError, msg="The value must be number"):
            self.lead.employes_number = "test"

    def test_80_field_headquarters_number(self):
        with self.assertRaises(ValueError, msg="The value must be number"):
            self.lead.headquarters_number = "test"

    def test_90_field_facturation(self):
        with self.assertRaises(ValueError, msg="The value must be number"):
            self.lead.facturation = "test"
