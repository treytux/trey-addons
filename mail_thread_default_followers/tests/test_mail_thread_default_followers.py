###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
# from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestMailThreadDefaultFollowers(TransactionCase):

    def setUp(self):
        super().setUp()

    def test_default_follower(self):
        partner = self.env['res.partner'].create({
            'name': 'Partner test'
        })
        self.assertTrue(partner.message_follower_ids)

    def test_none_follower(self):
        model = self.env['ir.model'].search([('model', '=', 'res.partner')])
        model.followers_setting = 'none'
        partner = self.env['res.partner'].create({
            'name': 'Partner test'
        })
        self.assertFalse(partner.message_follower_ids)
