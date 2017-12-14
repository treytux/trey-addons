# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common


class TestSaleLineWidgetGrid(common.TransactionCase):
    def setUp(self):
        super(TestSaleLineWidgetGrid, self).setUp()
        self.company = self.browse_ref('base.main_company')
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
        self.attribute1 = self.env['product.attribute'].create({
            'name': 'Test Attribute 1',
            'value_ids': [(0, 0, {'name': 'Value 1'}),
                          (0, 0, {'name': 'Value 2'})]})
        self.attribute2 = self.env['product.attribute'].create({
            'name': 'Test Attribute 2',
            'value_ids': [(0, 0, {'name': 'Value X'}),
                          (0, 0, {'name': 'Value Y'})]})
        self.product_tmpl = self.env['product.template'].create({
            'name': 'Test template',
            'attribute_line_ids': [
                (0, 0, {'attribute_id': self.attribute1.id,
                        'value_ids': [(6, 0, self.attribute1.value_ids.ids)]}),
                (0, 0, {'attribute_id': self.attribute2.id,
                        'value_ids': [
                            (6, 0, self.attribute2.value_ids.ids)]})]})

        # Check products has 4 variants
        assert len(self.product_tmpl.product_variant_ids) == 4
        self.order = self.env['sale.order'].create({
            'partner_id': self.partner_01.id,
            'pricelist_id': pricelist.id,
            'section_id': self.ref('sales_team.section_sales_department'),
            'picking_policy': 'direct',
            'date_order': '10/05/17',
            'note': 'Comment...',
            'company_id': self.company.id})
        self.order.onchange_partner_id(self.order.partner_id.id)
        # Wizard Usage
        self.Wizard = self.env['sale.manage.variant'].with_context(
            active_ids=self.order.ids, active_id=self.order.id,
            active_model=self.order._name)
        self.SaleOrderLine = self.env['sale.order.line']

    def test_same_product_lines_without_stock_quantity(self):
        # Stock quantity is checked by Javascript
        wizard = self.Wizard.create({'product_tmpl_id': self.product_tmpl.id})
        wizard._onchange_product_tmpl_id()
        self.assertEqual(len(wizard.variant_line_ids), 4)
        wizard.variant_line_ids[0].product_uom_qty = 1
        wizard.variant_line_ids[1].product_uom_qty = 2
        wizard.variant_line_ids[2].product_uom_qty = 3
        wizard.variant_line_ids[3].product_uom_qty = 4
        prod0 = wizard.variant_line_ids[0].product_id
        prod1 = wizard.variant_line_ids[1].product_id
        prod2 = wizard.variant_line_ids[2].product_id
        prod3 = wizard.variant_line_ids[3].product_id
        wizard.button_transfer_to_order()
        product_and_qtys = {prod0: 1, prod1: 2, prod2: 3, prod3: 4}
        self.assertEqual(len(self.order.order_line), 4,
                         'There should be 4 lines in the sale order')

        # test_same_qty_wizard_and_order_without_stock_quantity
        dict_prod = {}
        [dict_prod.update({line.product_id: line.product_uom_qty})
         for line in self.order.order_line]
        for n in dict_prod.keys():
            msn = ('Product %s not equal qty to both sides' % n.name)
            self.assertEqual(int(dict_prod[n]), product_and_qtys[n], msn)
