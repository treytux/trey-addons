###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestPartnerEmailUnique(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner_model = self.env['res.partner']
        self.company1 = self.env['res.company'].create({
            'name': 'Company test 1'
        })
        self.company2 = self.env['res.company'].create({
            'name': 'Company test 2'
        })
        self.partner = self.partner_model.create({
            'name': 'Test partner',
            'email': 'email@customer.com',
            'company_id': self.company1.id,
        })

    def test_duplicated_email_same_company(self):
        with self.assertRaises(ValidationError):
            self.partner_model.create({
                'name': 'Second partner',
                'email': 'email@customer.com',
                'company_id': self.company1.id,
            })

    def test_duplicated_email_different_company(self):
        self.partner_model.create({
            'name': 'Second partner',
            'email': 'email@customer.com',
            'company_id': self.company2.id,
        })

    def test_duplicated_email_creation_inactive(self):
        self.partner.active = False
        with self.assertRaises(ValidationError):
            self.env['res.partner'].create({
                'name': 'Second partner',
                'email': 'email@customer.com',
                'company_id': self.company1.id,
            })

    def test_duplicate_partner(self):
        partner_copied = self.partner.copy()
        self.assertFalse(partner_copied.email)
