# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common


class TestApi(common.TransactionCase):
    def setUp(self):
        super(TestApi, self).setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test partner'})
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
        assert len(self.product_tmpl.product_variant_ids) == 4
        self.order = self.env['sale.order'].create(
            {'partner_id': self.partner.id})
        self.order.onchange_partner_id(self.order.partner_id.id)
        self.Wizard = self.env['sale.manage.variant'].with_context(
            active_ids=self.order.ids, active_id=self.order.id,
            active_model=self.order._name)
        self.SaleOrderLine = self.env['sale.order.line']

    def test_add_variants(self):
        wizard = self.Wizard.create({'product_tmpl_id': self.product_tmpl.id})
        wizard._onchange_product_tmpl_id()
        self.assertEqual(len(wizard.variant_line_ids), 4)
        wizard.variant_line_ids[0].product_uom_qty = 1
        wizard.variant_line_ids[1].product_uom_qty = 2
        wizard.variant_line_ids[2].product_uom_qty = 3
        wizard.variant_line_ids[3].product_uom_qty = 4
        wizard.button_transfer_to_order()
        self.assertEqual(len(self.order.order_line), 4,
                         'There should be 4 lines in the sale order')

    # def test_modify_variants(self):
    #     product1 = self.product_tmpl.product_variant_ids[0]
    #     # order_line1 = self.SaleOrderLine.new({
    #     #     'order_id': self.order.id,
    #     #     'product_id': product1.id,
    #     #     'product_uom_qty': 1})
    #     order_line1 = self.SaleOrderLine.create({
    #         'order_id': self.order.id,
    #         'product_id': product1.id,
    #         'product_uom_qty': 1})
    #     order_line1.product_id_change(
    #         self.order.pricelist_id.id, product1.id, qty=1,
    #         partner_id=self.order.partner_id.id)
    #     product2 = self.product_tmpl.product_variant_ids[1]
    #     order_line1 = self.SaleOrderLine.create(
    #         order_line1._convert_to_write(order_line1._cache))
    #     # order_line2 = self.SaleOrderLine.new({
    #     #     'order_id': self.order.id,
    #     #     'product_id': product2.id,
    #     #     'product_uom_qty': 2})
    #     order_line2 = self.SaleOrderLine.create({
    #         'order_id': self.order.id,
    #         'product_id': product2.id,
    #         'product_uom_qty': 2})
    #     order_line2.product_id_change(
    #         self.order.pricelist_id.id, product2.id, qty=1,
    #         partner_id=self.order.partner_id.id)
    #     order_line2 = self.SaleOrderLine.create(
    #         order_line2._convert_to_write(order_line2._cache))
    #     Wizard2 = self.Wizard.with_context(
    #         default_product_tmpl_id=self.product_tmpl.id,
    #         active_model='sale.order.line',
    #         active_id=order_line1.id, active_ids=order_line1.ids)
    #     wizard = Wizard2.create({})
    #     wizard._onchange_product_tmpl_id()
    #     self.assertEqual(
    #         len(wizard.variant_line_ids.filtered('product_uom_qty')), 2,
    #         "There should be two fields with any quantity in the wizard.")
    #     wizard.variant_line_ids.filtered(
    #         lambda x: x.product_id == product1).product_uom_qty = 0
    #     wizard.variant_line_ids.filtered(
    #         lambda x: x.product_id == product2).product_uom_qty = 10
    #     wizard.button_transfer_to_order()
    #     self.assertFalse(order_line1.exists(), "Order line not removed.")
        # self.assertEqual(
        #     order_line2.product_uom_qty, 10,
        #     "Order line not change quantity.")
