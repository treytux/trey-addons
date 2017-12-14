# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common
from openerp import fields, tools
import os
import logging
_log = logging.getLogger(__name__)


class TestPrintFormatsStock(common.TransactionCase):
    def setUp(self):
        super(TestPrintFormatsStock, self).setUp()
        self.company = self.env['res.company'].create({
            'name': 'CompanyCompany',
            'street': 'Calle poniente, 3',
            'custom_header': True,
            'report_header': 'Yes! My company'})

        self.pt_01 = self.env['product.template'].create({
            'name': 'Product 01',
            'type': 'consu'})
        self.pp_01 = self.env['product.product'].create({
            'product_tmpl_id': self.pt_01.id,
            'default_code': '123456'})

        self.partner_01 = self.env['res.partner'].create({
            'name': 'Customer 01',
            'is_company': True,
            'customer': True,
            'email': 'customer1@test.com',
            'street': 'Calle Real, 33',
            'phone': '666225522'})

        self.secuence = self.env['ir.sequence'].create({
            'name': 'Your Company Sequence in',
            'prefix': 'W1',
            'active': True,
            'padding': 5,
            'number_next_actual': 2,
            'number_increment': 1,
            'implementation': 'standard'})

        self.stock_location = self.env['stock.location'].create({
            'name': 'existencias',
            'usage': 'internal',
            'active': True})

        self.location = self.env['stock.location'].create({
            'name': 'existences source',
            'usage': 'internal',
            'active': True})

        self.stock_picking_type = self.env['stock.picking.type'].create({
            'name': 'Recepciones',
            'sequence_id': self.secuence.id,
            'code': 'incoming',
            'default_location_dest_id': self.stock_location.id})

        self.stock_picking = self.env['stock.picking'].create({
            'partner_id': self.partner_01.id,
            'date': fields.Date.today(),
            'origin': 'POE12',
            'note': 'Comment...',
            'state': 'confirmed',
            'move_type': 'direct',
            'invoice_state': '2binvoiced',
            'picking_type_id': self.stock_picking_type.id,
            'priority': '1'})

        self.taxs_21 = self.env['account.tax'].create({
            'name': '%21%',
            'type': 'percent',
            'amount': 0.21,
            'type_tax_use': 'all',
            'applicable_type': 'true',
            'sequence': 1,
            'company_id': self.company.id})

        self.move_line = self.env['stock.move'].create({
            'picking_id': self.stock_picking.id,
            'product_id': self.pp_01.id,
            'product_uom_qty': 1,
            'name': 'Description 1',
            'date': fields.Date.today(),
            'date_expected': fields.Date.today(),
            'price_unit': 33.25,
            'location_dest_id': self.stock_location.id,
            'location_id': self.location.id,
            'product_uom': self.ref('product.product_uom_unit'),
            'company_id': self.company.id})

    def print_report(self, obj, rname, fname):
        pdf = self.env['report'].get_pdf(obj, rname)
        with open(fname, 'w') as fp:
            fp.write(pdf)

    def test_print_formats_stock(self):
        instance_path = os.path.join(
            tools.config['test_report_directory'],
            'test_print_formats_stock_picking.pdf')
        self.print_report(
            self.stock_picking, 'stock.report_picking',
            instance_path)
