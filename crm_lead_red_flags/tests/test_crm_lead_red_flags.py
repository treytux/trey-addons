###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import psycopg2
from odoo.tests.common import TransactionCase


class CrmLeadRedFlags(TransactionCase):

    def setUp(self):
        super().setUp()
        self.red_flag = self.env['crm.lead.red.flag'].create({
            'name' : 'Test Red Flag 1',
        })
        self.lead = self.env['crm.lead'].create({
            'name': 'Test Lead',
            'red_flag_ids': [(4, self.red_flag.id)],
        })

    def test_assign_lead_red_flags(self):
        self.assertEqual(self.lead.red_flag_ids, self.red_flag)

    def test_unique_name_red_flag(self):
        with self.assertRaises(psycopg2.IntegrityError):
            self.env['crm.lead.red.flag'].create({
                'name' : 'Test Red Flag 1',
            })

    def test_field_red_flag_ids_crm(self):
        with self.assertRaises(ValueError):
            self.lead.red_flag_ids = "String"

    def test_assign_field_name_red_flag(self):
        red_flag = self.env['crm.lead.red.flag'].create({
            'name': 'Test Red Flag 2',
        })
        self.assertEqual(red_flag.name, 'Test Red Flag 2')
