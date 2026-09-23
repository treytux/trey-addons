###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestStockPickingEditWizard(TransactionCase):

    def setUp(self):
        super().setUp()
        self.picking_type = self.env.ref('stock.picking_type_in')
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
        })
        self.picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type.id,
            'partner_id': self.partner.id,
            'location_id': self.env.ref('stock.stock_location_suppliers').id,
            'location_dest_id': self.env.ref('stock.stock_location_stock').id,
        })

    def test_default_get(self):
        wizard = self.env['stock.picking.edit_wizard'].with_context(
            active_id=self.picking.id
        ).create({})
        self.assertEqual(wizard.number, self.picking.name)
        self.assertEqual(wizard.date, fields.Date.to_date(self.picking.date))

    def test_button_save(self):
        new_date = fields.Date.to_date('2024-01-15')
        wizard = self.env['stock.picking.edit_wizard'].with_context(
            active_id=self.picking.id
        ).create({
            'number': 'TEST0001',
            'date': new_date,
        })
        wizard.button_save()
        self.assertEqual(self.picking.name, 'TEST0001')
        self.assertEqual(
            fields.Date.to_date(self.picking.scheduled_date), new_date)

    def test_button_save_duplicate_number(self):
        duplicate = self.picking.copy({
            'name': 'DUPLICATE',
        })
        wizard = self.env['stock.picking.edit_wizard'].with_context(
            active_id=self.picking.id
        ).create({
            'number': duplicate.name,
        })
        with self.assertRaises(UserError):
            wizard.button_save()
