###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime

from dateutil.relativedelta import relativedelta
from odoo import fields
from odoo.tests import TransactionCase


class TestStockPickingGeneratorWizard(TransactionCase):
    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer',
        })
        self.wizard = self.env['stock.picking.generator.wizard'].create({
            'product': self.product.id,
            'partner_id': self.partner.id,
            'quantity': 3,
            'period': 1,
            'period_unit': 'days',
        })
        self.picking_type = self.env.ref(
            'stock_picking_generator_wizard.stock_picking_type_ts_test')

    def test_correct_number_of_pickings(self):
        action = self.wizard.action_create_pickings()
        pickings = self.env['stock.picking'].search([
            ('id', 'in', action['domain'][0][2]),
        ])
        self.assertEqual(len(pickings), self.wizard.quantity)

    def test_scheduled_dates_days(self):
        self.wizard.period_unit = 'days'
        base = datetime.utcnow().replace(microsecond=0)
        action = self.wizard.action_create_pickings()
        pickings = self.env['stock.picking'].browse(action['domain'][0][2])
        for i, picking in enumerate(pickings):
            expected = base + relativedelta(days=self.wizard.period * i)
            self.assertEqual(
                fields.Datetime.to_datetime(picking.scheduled_date), expected)

    def test_scheduled_dates_months(self):
        self.wizard.period_unit = 'months'
        base = datetime.utcnow().replace(microsecond=0)
        action = self.wizard.action_create_pickings()
        pickings = self.env['stock.picking'].browse(action['domain'][0][2])
        for i, picking in enumerate(pickings):
            expected = base + relativedelta(months=self.wizard.period * i)
            self.assertEqual(
                fields.Datetime.to_datetime(picking.scheduled_date), expected)

    def test_scheduled_dates_years(self):
        self.wizard.period_unit = 'years'
        base = datetime.utcnow().replace(microsecond=0)
        action = self.wizard.action_create_pickings()
        pickings = self.env['stock.picking'].browse(action['domain'][0][2])
        for i, picking in enumerate(pickings):
            expected = base + relativedelta(years=self.wizard.period * i)
            self.assertEqual(
                fields.Datetime.to_datetime(picking.scheduled_date), expected)

    def test_picking_content(self):
        action = self.wizard.action_create_pickings()
        pickings = self.env['stock.picking'].browse(action['domain'][0][2])
        for picking in pickings:
            self.assertEqual(picking.partner_id, self.partner)
            self.assertEqual(len(picking.move_ids), 1)
            move = picking.move_ids
            self.assertEqual(move.product_id, self.product)
            self.assertEqual(move.product_uom_qty, 1.0)
            self.assertEqual(
                move.location_id, self.picking_type.default_location_src_id)
            self.assertEqual(
                move.location_dest_id,
                self.picking_type.default_location_dest_id)

    def test_action_domain(self):
        action = self.wizard.action_create_pickings()
        self.assertEqual(action['res_model'], 'stock.picking')
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['domain'][0][0], 'id')
        self.assertEqual(action['domain'][0][1], 'in')
        self.assertEqual(len(action['domain'][0][2]), self.wizard.quantity)
