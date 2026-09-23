###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import Form, TransactionCase


class TestStockPickingEditNumber(TransactionCase):

    def setUp(self):
        super().setUp()
        self.picking_type_in = self.env.ref('stock.picking_type_in')
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
        })
        self.picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type_in.id,
            'partner_id': self.partner.id,
            'location_id': self.env.ref('stock.stock_location_suppliers').id,
            'location_dest_id': self.env.ref('stock.stock_location_stock').id,
        })

    def test_default_get(self):
        wizard = Form(self.env['stock.picking.edit_wizard'].with_context(
            active_id=self.picking.id, active_model='stock.picking'))
        self.assertEqual(wizard.number, self.picking.name)
        self.assertEqual(wizard.date, fields.Date.to_date(self.picking.date))

    def test_button_save(self):
        new_date = fields.Date.to_date('2024-01-15')
        wizard = Form(self.env['stock.picking.edit_wizard'].with_context(
            active_id=self.picking.id, active_model='stock.picking'))
        wizard.number = 'TEST0001'
        wizard.date = new_date
        wizard = wizard.save()
        wizard.button_save()
        self.assertEqual(self.picking.name, 'TEST0001')
        self.assertEqual(
            fields.Date.to_date(self.picking.scheduled_date), new_date)

    def test_button_save_duplicate_number(self):
        duplicate = self.picking.copy({
            'name': 'DUPLICATE',
        })
        wizard = Form(self.env['stock.picking.edit_wizard'].with_context(
            active_id=self.picking.id, active_model='stock.picking'))
        wizard.number = duplicate.name
        wizard = wizard.save()
        with self.assertRaises(UserError):
            wizard.button_save()

    def test_required_number(self):
        wizard = Form(self.env['stock.picking.edit_wizard'].with_context(
            active_id=self.picking.id, active_model='stock.picking'))
        wizard.number = False
        with self.assertRaises(AssertionError) as context:
            wizard.save()
        self.assertIn('number is a required field', str(context.exception))

    def test_required_date(self):
        wizard = Form(self.env['stock.picking.edit_wizard'].with_context(
            active_id=self.picking.id, active_model='stock.picking'))
        wizard.date = False
        with self.assertRaises(AssertionError) as context:
            wizard.save()
        self.assertIn('date is a required field', str(context.exception))

    def test_empty_active_id_no_change(self):
        original_name = self.picking.name
        original_date = self.picking.scheduled_date
        wizard = Form(self.env['stock.picking.edit_wizard'].with_context(
            active_id=None, active_model='stock.picking'))
        wizard.number = 'TEST0001'
        wizard.date = fields.Date.to_date('2024-01-15')
        wizard = wizard.save()
        result = wizard.button_save()
        self.assertEqual(result, {'type': 'ir.actions.act_window_close'})
        self.assertEqual(self.picking.name, original_name)
        self.assertEqual(self.picking.scheduled_date, original_date)
