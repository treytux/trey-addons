###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from unittest.mock import patch

from odoo.addons.sale.models.sale_order import SaleOrder as SaleOrderModel
from odoo.tests.common import TransactionCase


class TestSaleOrderNotifyGroups(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner Test Notify Groups',
        })
        self.sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })

    def test_user_group_keeps_has_button_access(self):
        groups = [
            ('user', [], {'has_button_access': True}),
        ]
        with patch.object(
            SaleOrderModel,
                '_notify_get_recipients_groups', return_value=groups):
            result = self.sale._notify_get_recipients_groups()
        self.assertTrue(result[0][2]['has_button_access'])

    def test_non_user_groups_lose_has_button_access_when_true(self):
        groups = [
            ('follower', [], {'has_button_access': True}),
            ('portal', [], {'has_button_access': True}),
            ('customer', [], {'has_button_access': False}),
        ]
        with patch.object(
            SaleOrderModel,
                '_notify_get_recipients_groups', return_value=groups):
            result = self.sale._notify_get_recipients_groups()
        self.assertFalse(result[0][2]['has_button_access'])
        self.assertFalse(result[1][2]['has_button_access'])
        self.assertFalse(result[2][2]['has_button_access'])

    def test_group_without_has_button_access_is_unchanged(self):
        groups = [
            ('portal_customer', [], {'custom_key': 'value'}),
        ]
        with patch.object(
            SaleOrderModel,
                '_notify_get_recipients_groups', return_value=groups):
            result = self.sale._notify_get_recipients_groups()
        self.assertEqual(result[0][2], {'custom_key': 'value'})
        self.assertNotIn('has_button_access', result[0][2])
