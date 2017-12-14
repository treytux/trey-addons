# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common
from openerp import fields


class SaleOrderJoin(common.TransactionCase):
    def setUp(self):
        super(SaleOrderJoin, self).setUp()
        self.company = self.browse_ref('base.main_company')
        self.company2 = self.env['res.company'].create({
            'name': 'CompanyCompany',
            'custom_header': True,
            'report_header': 'Yes! My company'})
        tax_21 = self.env['account.tax'].create({
            'name': '%21%',
            'type': 'percent',
            'amount': 0.21,
            'type_tax_use': 'all',
            'applicable_type': 'true',
            'sequence': 1,
            'company_id': self.company.id})
        tax_21 = self.env['account.tax'].create({
            'name': '%21%',
            'type': 'percent',
            'amount': 0.21,
            'type_tax_use': 'all',
            'applicable_type': 'true',
            'sequence': 1,
            'company_id': self.company2.id})
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
        self.partner_01 = self.env['res.partner'].create({
            'name': 'Customer 01',
            'is_company': True,
            'customer': True,
            'email': 'customer1@test.com',
            'street': 'Calle Real, 33',
            'phone': '666225522'})
        self.pt_01 = self.env['product.template'].create({
            'name': 'Product 01',
            'type': 'product',
            'list_price': 10,
            'taxes_id': [(6, 0, [tax_21.id])]})
        self.pp_01 = self.env['product.product'].create(
            {'product_tmpl_id': self.pt_01.id})
        self.pt_02 = self.env['product.template'].create({
            'name': 'Product 02',
            'type': 'product',
            'list_price': 20,
            'taxes_id': [(6, 0, [tax_21.id])]})
        self.pp_02 = self.env['product.product'].create(
            {'product_tmpl_id': self.pt_02.id})
        self.pt_03 = self.env['product.template'].create({
            'name': 'Product 03',
            'type': 'product',
            'list_price': 15,
            'taxes_id': [(6, 0, [tax_21.id])]})
        self.pp_03 = self.env['product.product'].create(
            {'product_tmpl_id': self.pt_03.id})
        pricelist = self.env['product.pricelist'].create({
            'name': '10% discount',
            'type': 'sale'})
        version = self.env['product.pricelist.version'].create({
            'pricelist_id': pricelist.id,
            'name': '10% discount version'})
        self.env['product.pricelist.item'].create({
            'price_version_id': version.id,
            'name': '10% discount item',
            'sequence': 10,
            'base': self.ref('product.list_price'),
            'price_discount': -0.1})

        self.order_01 = self.env['sale.order'].create({
            'partner_id': self.partner_01.id,
            'pricelist_id': pricelist.id,
            'section_id': self.ref('sales_team.section_sales_department'),
            'picking_policy': 'direct',
            'picking_type_id': self.stock_picking_type.id,
            'date_order': '10/10/15',
            'note': 'Comment...',
            'company_id': self.company.id})
        self.order_line_1_1 = self.env['sale.order.line'].create({
            'order_id': self.order_01.id,
            'product_id': self.pp_01.id,
            'product_uom_qty': 1,
            'price_unit': self.pp_01.product_tmpl_id.list_price,
            'tax_id': [(6, 0, [tax_21.id])]})
        self.order_line_1_2 = self.env['sale.order.line'].create({
            'order_id': self.order_01.id,
            'product_id': self.pp_02.id,
            'product_uom_qty': 3,
            'price_unit': self.pp_02.product_tmpl_id.list_price,
            'tax_id': [(6, 0, [tax_21.id])]})

        self.order_02 = self.env['sale.order'].create({
            'partner_id': self.partner_01.id,
            'pricelist_id': self.ref('product.list0'),
            'date_order': fields.Date.today(),
            'section_id': self.ref('sales_team.section_sales_department'),
            'picking_policy': 'direct',
            'picking_type_id': self.stock_picking_type.id,
            'note': 'Comment...',
            'company_id': self.company.id,
            'client_order_ref': '016/81601863/ BM PALMA DE MALLORCA'})
        self.order_line_2_1 = self.env['sale.order.line'].create({
            'order_id': self.order_02.id,
            'product_id': self.pp_02.id,
            'discount': 0.1,
            'product_uom_qty': 1,
            'price_unit': self.pp_02.product_tmpl_id.list_price,
            'tax_id': [(6, 0, [tax_21.id])]})
        self.order_line_2_2 = self.env['sale.order.line'].create({
            'order_id': self.order_02.id,
            'product_id': self.pp_03.id,
            'product_uom_qty': 4,
            'price_unit': self.pp_03.product_tmpl_id.list_price,
            'tax_id': [(6, 0, [tax_21.id])]})

        self.order_03 = self.env['sale.order'].create({
            'partner_id': self.partner_01.id,
            'pricelist_id': pricelist.id,
            'section_id': self.ref('sales_team.section_sales_department'),
            'picking_policy': 'direct',
            'picking_type_id': self.stock_picking_type.id,
            'date_order': '10/10/15',
            'note': 'Comment...',
            'company_id': self.company2.id})
        self.order_line_1_1 = self.env['sale.order.line'].create({
            'order_id': self.order_03.id,
            'product_id': self.pp_01.id,
            'product_uom_qty': 1,
            'price_unit': self.pp_01.product_tmpl_id.list_price,
            'tax_id': [(6, 0, [tax_21.id])]})
        self.order_line_1_2 = self.env['sale.order.line'].create({
            'order_id': self.order_03.id,
            'product_id': self.pp_02.id,
            'product_uom_qty': 3,
            'price_unit': self.pp_02.product_tmpl_id.list_price,
            'tax_id': [(6, 0, [tax_21.id])]})

        self.order_04 = self.env['sale.order'].create({
            'partner_id': self.partner_01.id,
            'pricelist_id': self.ref('product.list0'),
            'date_order': fields.Date.today(),
            'section_id': self.ref('sales_team.section_sales_department'),
            'picking_policy': 'direct',
            'picking_type_id': self.stock_picking_type.id,
            'note': 'Comment...',
            'company_id': self.company2.id,
            'client_order_ref': '016/81601863/ BM PALMA DE MALLORCA'})
        self.order_line_2_1 = self.env['sale.order.line'].create({
            'order_id': self.order_04.id,
            'product_id': self.pp_02.id,
            'discount': 0.1,
            'product_uom_qty': 1,
            'price_unit': self.pp_02.product_tmpl_id.list_price,
            'tax_id': [(6, 0, [tax_21.id])]})
        self.order_line_2_2 = self.env['sale.order.line'].create({
            'order_id': self.order_04.id,
            'product_id': self.pp_03.id,
            'product_uom_qty': 4,
            'price_unit': self.pp_03.product_tmpl_id.list_price,
            'tax_id': [(6, 0, [tax_21.id])]})

    def test_sale_order_join1_different_partners(self):
        self.env['wiz.sale.order.join'].with_context(
            active_ids=[self.order_01.id, self.order_02.id,
                        self.order_03.id, self.order_04.id],
            active_model='sale.order',
            active_id=self.order_01.id).create({
                'active_ids': [
                    self.order_01.id, self.order_02.id, self.order_03.id,
                    self.order_04.id]}).button_accept()
        self.assertEqual(len(self.order_01.order_line), 8)
