# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields
import openerp.tests.common as common


class TestEdifactStockPicking(common.TransactionCase):

    def setUp(self):
        super(TestEdifactStockPicking, self).setUp()
        self.edifact_document1 = self.env['edifact.document'].create({
            'name': 'test',
            'ttype': 'picking'})
        self.partner_01 = self.env['res.partner'].create({
            'name': 'Customer 01',
            'is_company': True,
            'customer': True,
            'email': 'customer1@test.com',
            'street': 'Calle Real, 33',
            'phone': '666225522',
            'ean13': '8422416000001',
            'city': 'Madrid',
            'zip': '12345',
            'vat': 'ESA28017895'})
        self.product_01 = self.env['product.product'].create({
            'name': 'Product 01',
            'ean13': '0075678164125',
            'default_code': 'COD-PROD-1'})
        self.product_02 = self.env['product.product'].create({
            'name': 'Product 02',
            'ean13': '0000000350006',
            'default_code': 'COD-PROD-2'})
        self.product_03 = self.env['product.product'].create({
            'name': 'Product 03',
            'default_code': 'COD-PROD-3'})
        self.stock_location = self.env['stock.location'].create({
            'name': 'existencias',
            'usage': 'internal',
            'active': True})
        self.location = self.env['stock.location'].create({
            'name': 'existences source',
            'usage': 'internal',
            'active': True})
        self.stock_picking = self.env['stock.picking'].create({
            'partner_id': self.partner_01.id,
            'date': fields.Datetime.now(),
            'origin': 'SO076',
            'note': 'Comment...',
            'state': 'confirmed',
            'move_type': 'direct',
            'invoice_state': '2binvoiced',
            'picking_type_id': self.ref('stock.picking_type_out'),
            'priority': '1',
            'company_id': self.ref('base.main_company')})
        self.move_01 = self.env['stock.move'].create({
            'picking_id': self.stock_picking.id,
            'product_id': self.product_01.id,
            'product_uom_qty': 3,
            'name': self.product_01.name,
            'date': fields.Datetime.now(),
            'date_expected': fields.Date.today(),
            'price_unit': 33.25,
            'product_uom': self.env.ref('product.product_uom_unit').id,
            'location_dest_id': self.stock_location.id,
            'location_id': self.location.id,
            'company_id': self.ref('base.main_company')})
        self.move_02 = self.env['stock.move'].create({
            'picking_id': self.stock_picking.id,
            'product_id': self.product_02.id,
            'product_uom_qty': 3,
            'name': self.product_02.name,
            'date': fields.Datetime.now(),
            'date_expected': fields.Date.today(),
            'price_unit': 33.25,
            'product_uom': self.env.ref('product.product_uom_unit').id,
            'location_dest_id': self.stock_location.id,
            'location_id': self.location.id,
            'company_id': self.ref('base.main_company')})

    def test_export_pickings(self):
        self.edifact_document1.process_picking_out_files(
            self.stock_picking)
