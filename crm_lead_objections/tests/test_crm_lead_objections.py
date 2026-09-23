###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import psycopg2
from odoo.tests.common import TransactionCase


class CrmLeadObjections(TransactionCase):

    def setUp(self):
        super().setUp()
        lead_obj = self.env['crm.lead']
        self.objection_obj = self.env['crm.lead.objection']
        self.objection = self.objection_obj.create({
            'name' : 'prueba1',
        })
        self.lead = lead_obj.create({
            'name' : 'lead_prueba'
        })

    def test_unique_name_objection(self):
        with self.assertRaises(psycopg2.IntegrityError):
            self.objection_obj.create({
                'name' : 'prueba1'
            })

    def test_objections_field(self):
        with self.assertRaises(ValueError):
            self.lead.objection_ids = 123

    def test_create_and_assign_lead_objection(self):
        objection = self.objection_obj.create({
            'name' : 'prueba2',
        })
        self.lead.write({
            'objection_ids': [(6, 0, [objection.id])],
        })
