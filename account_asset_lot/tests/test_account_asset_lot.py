###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.tests import common


class TestAccountAssetLot(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.account_expense = self.env['account.account'].create({
            'code': 'X2120',
            'name': 'Expenses test',
            'account_type': 'expense',
        })
        self.account_xfa = self.env['account.account'].create({
            'code': 'X1000',
            'name': 'Fixed assets tests',
            'account_type': 'asset_fixed',
        })
        self.expenses_journal = self.env['account.journal'].create({
            'name': 'Test journal for sale',
            'type': 'sale',
            'code': 'TSALE',
            'default_account_id': self.account_expense.id,
        })
        self.asset_profile = self.env['account.asset.profile'].create({
            'account_expense_depreciation_id': self.account_expense.id,
            'account_asset_id': self.account_xfa.id,
            'account_depreciation_id': self.account_xfa.id,
            'journal_id': self.expenses_journal.id,
            'name': 'Test profile',
            'method_time': 'year',
            'method_number': 5,
            'method_period': 'year',
        })
        self.asset = self.env['account.asset'].create({
            'code': 'CODE-TEST-1234',
            'date_start': fields.Date.today(),
            'method': 'linear',
            'method_period': 'year',
            'method_time': 'year',
            'method_number': 5,
            'name': 'Asset test',
            'profile_id': self.asset_profile.id,
            'purchase_value': 20000,
            'state': 'open',
            'note': 'Notes for asset test',
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'name': 'Service product',
            'tracking': 'serial',
        })
        self.lot = self.env['stock.lot'].create({
            'product_id': self.product.id,
        })
        self.location = self.env['stock.location'].create({
            'name': 'Location test',
            'usage': 'internal',
        })

    def create_inventory(self, location, lot, qty):
        self.env['stock.quant'].with_context(inventory_mode=True).create({
            'product_id': lot.product_id.id,
            'location_id': location.id,
            'lot_id': lot.id,
            'inventory_quantity': qty,
        }).action_apply_inventory()

    def test_account_asset_related_lot(self):
        self.assertFalse(self.asset.lot_id)
        self.assertFalse(self.asset.location_id)
        self.create_inventory(self.location, self.lot, 1)
        quants = self.env['stock.quant'].search([
            ('lot_id', '=', self.lot.id),
        ])
        self.assertEqual(len(quants), 2)
        quant = quants.filtered(lambda q: q.quantity == 1)
        self.assertEqual(quant.quantity, 1)
        self.asset.lot_id = self.lot.id
        self.assertTrue(self.asset.lot_id)
        self.assertEqual(self.asset.lot_id, self.lot)
        self.assertTrue(self.asset.location_id)
        self.assertEqual(self.asset.location_id, self.location)
