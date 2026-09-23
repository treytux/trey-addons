###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class ResPartnerBankNoUnique(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner_model = self.env['res.partner']
        self.partner_1 = self.partner_model.create({
            'name': 'Test partner 1',
            'email': 'email_1@customer.com',
        })
        self.partner_2 = self.partner_model.create({
            'name': 'Test partner 2',
            'email': 'email_2@customer.com',
        })

    def test_duplicated_partner_bank(self):
        self.partner_1.write({
            'bank_ids': [(0, 0, {
                'acc_number': 'ES00 0000 0000 0000 0000 1111',
            })]
        })
        self.partner_2.write({
            'bank_ids': [(0, 0, {
                'acc_number': 'ES00 0000 0000 0000 0000 1111',
            })]
        })
        self.assertEquals(
            self.partner_1.bank_ids[0].acc_number,
            self.partner_2.bank_ids[0].acc_number)
