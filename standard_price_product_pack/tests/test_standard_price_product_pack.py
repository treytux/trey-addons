###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestSaleStockProductPack(TransactionCase):
    def setUp(self):
        super().setUp()
        self.product_tmpl_obj = self.env['product.template']
        self.partner = self.env['res.partner'].create({
            'name': 'Customer',
            'customer': True,
        })
        self.product_tmp_1 = self.product_tmpl_obj.create({
            'name': 'Component 1',
            'type': 'consu',
            'list_price': 150,
            'standard_price': 50,
        })
        self.product_tmpl_2 = self.product_tmpl_obj.create({
            'name': 'Component 2',
            'type': 'consu',
            'list_price': 200,
            'standard_price': 100,
        })
        self.product_tmpl_3 = self.product_tmpl_obj.create({
            'name': 'Component 3',
            'type': 'consu',
            'list_price': 250,
            'standard_price': 150,
        })
        self.product_pack_totalized = self.product_tmpl_obj.create({
            'name': 'Pack totalized',
            'type': 'consu',
            'list_price': 1000,
            'pack_ok': True,
            'pack_type': 'detailed',
            'pack_component_price': 'ignored',
            'pack_component_cost': 'totalized',
            'standard_price': 250,
        })
        self.product_pack_detailed = self.product_tmpl_obj.create({
            'name': 'Pack detailed',
            'type': 'consu',
            'list_price': 2000,
            'pack_ok': True,
            'pack_type': 'detailed',
            'pack_component_price': 'ignored',
            'pack_component_cost': 'detailed',
            'standard_price': 500,
        })
        self.product_pack_ignored = self.product_tmpl_obj.create({
            'name': 'Pack ignored',
            'type': 'consu',
            'list_price': 3000,
            'pack_ok': True,
            'pack_type': 'detailed',
            'pack_component_price': 'ignored',
            'pack_component_cost': 'ignored',
            'standard_price': 750,
        })

    def test_product_packs_standard_prices(self):
        self.assertEquals(self.product_tmp_1.standard_price, 50)
        self.assertEquals(self.product_tmpl_2.standard_price, 100)
        self.assertEquals(self.product_tmpl_3.standard_price, 150)
        self.assertEquals(self.product_pack_totalized.standard_price, 250)
        self.product_pack_totalized.write({
            'pack_line_ids': [
                (0, 0, {
                    'product_id': self.product_tmp_1.product_variant_ids.id,
                    'quantity': 1,
                }),
                (0, 0, {
                    'product_id': self.product_tmpl_2.product_variant_ids.id,
                    'quantity': 2,
                }),
            ],
        })
        self.assertEquals(self.product_tmp_1.standard_price, 50)
        self.assertEquals(self.product_tmpl_2.standard_price, 100)
        self.assertEquals(self.product_pack_totalized.standard_price, 250)
        self.product_tmp_1.write({
            'standard_price': 100
        })
        self.assertEquals(self.product_pack_totalized.standard_price, 300)
        self.product_tmp_1.standard_price = 50
        self.product_pack_totalized.pack_line_ids = False
        self.assertEquals(self.product_pack_totalized.standard_price, 250)
        self.assertEquals(self.product_pack_detailed.standard_price, 500)
        self.product_pack_detailed.write({
            'pack_line_ids': [
                (0, 0, {
                    'product_id': self.product_tmpl_2.product_variant_ids.id,
                    'quantity': 1,
                }),
                (0, 0, {
                    'product_id': self.product_tmpl_3.product_variant_ids.id,
                    'quantity': 2,
                }),
            ],
        })
        self.assertEquals(self.product_tmpl_2.standard_price, 100)
        self.assertEquals(self.product_tmpl_3.standard_price, 150)
        self.assertEquals(self.product_pack_detailed.standard_price, 500)
        self.product_pack_detailed.pack_line_ids = False
        self.assertEquals(self.product_pack_detailed.standard_price, 500)
        self.assertEquals(self.product_pack_ignored.standard_price, 750)
        self.product_pack_ignored.write({
            'pack_line_ids': [
                (0, 0, {
                    'product_id': self.product_tmpl_2.product_variant_ids.id,
                    'quantity': 1,
                }),
                (0, 0, {
                    'product_id': self.product_tmpl_3.product_variant_ids.id,
                    'quantity': 2,
                }),
            ],
        })
        self.assertEquals(self.product_tmp_1.standard_price, 50)
        self.assertEquals(self.product_tmpl_3.standard_price, 150)
        self.assertEquals(self.product_pack_ignored.standard_price, 750)
        self.product_pack_ignored.pack_line_ids = False
        self.assertEquals(self.product_pack_ignored.standard_price, 750)

    def test_sale_product_pack_detailed(self):
        self.assertEquals(self.product_tmp_1.standard_price, 50)
        self.assertEquals(self.product_tmpl_2.standard_price, 100)
        self.assertEquals(self.product_pack_detailed.standard_price, 500)
        self.product_pack_detailed.write({
            'pack_line_ids': [
                (0, 0, {
                    'product_id': self.product_tmp_1.product_variant_ids.id,
                    'quantity': 1,
                }),
                (0, 0, {
                    'product_id': self.product_tmpl_2.product_variant_ids.id,
                    'quantity': 1,
                }),
            ],
        })
        self.assertEquals(self.product_tmp_1.standard_price, 50)
        self.assertEquals(self.product_tmpl_2.standard_price, 100)
        self.assertEquals(self.product_pack_detailed.standard_price, 500)
        variant_pack_detailed_id = (
            self.product_pack_detailed.product_variant_ids.id)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': variant_pack_detailed_id,
                    'product_uom_qty': 1,
                }),
            ]
        })
        for line in sale.order_line:
            line.product_id_change()
            self.assertEquals(
                line.purchase_price, line.product_id.standard_price)
        self.assertEquals(len(sale.order_line), 3)
        self.assertEquals(sale.margin, 1700)

    def test_sale_product_pack_ignored(self):
        self.assertEquals(self.product_tmp_1.standard_price, 50)
        self.assertEquals(self.product_tmpl_2.standard_price, 100)
        self.assertEquals(self.product_pack_ignored.standard_price, 750)
        self.product_pack_ignored.write({
            'pack_line_ids': [
                (0, 0, {
                    'product_id': self.product_tmp_1.product_variant_ids.id,
                    'quantity': 1,
                }),
                (0, 0, {
                    'product_id': self.product_tmpl_2.product_variant_ids.id,
                    'quantity': 1,
                }),
            ],
        })
        self.assertEquals(self.product_tmp_1.standard_price, 50)
        self.assertEquals(self.product_tmpl_2.standard_price, 100)
        self.assertEquals(self.product_pack_ignored.standard_price, 750)
        variant_pack_ignored_id = (
            self.product_pack_ignored.product_variant_ids.id)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': variant_pack_ignored_id,
                    'product_uom_qty': 1,
                }),
            ]
        })
        self.assertEquals(sale.order_line[0].purchase_price, 750)
        for line in sale.order_line.filtered('pack_parent_line_id'):
            line.product_id_change()
            self.assertEquals(line.purchase_price, 0.0)
        self.assertEquals(len(sale.order_line), 3)
        self.assertEquals(sale.margin, 2600)

    def test_sale_product_pack_totalized(self):
        self.assertEquals(self.product_tmpl_2.standard_price, 100)
        self.assertEquals(self.product_tmpl_3.standard_price, 150)
        self.assertEquals(self.product_pack_totalized.standard_price, 250)
        self.product_pack_totalized.write({
            'pack_line_ids': [
                (0, 0, {
                    'product_id': self.product_tmpl_2.product_variant_ids.id,
                    'quantity': 1,
                }),
                (0, 0, {
                    'product_id': self.product_tmpl_3.product_variant_ids.id,
                    'quantity': 2,
                }),
            ],
        })
        self.assertEquals(self.product_tmpl_2.standard_price, 100)
        self.assertEquals(self.product_tmpl_3.standard_price, 150)
        self.assertEquals(self.product_pack_totalized.standard_price, 400)
        variant_pack_totalized_id = (
            self.product_pack_totalized.product_variant_ids.id)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': variant_pack_totalized_id,
                    'product_uom_qty': 2,
                }),
            ]
        })
        self.assertEquals(sale.order_line[0].purchase_price, 250)
        for line in sale.order_line.filtered('pack_parent_line_id'):
            line.product_id_change()
            self.assertEquals(line.purchase_price, 0.0)
        self.assertEquals(len(sale.order_line), 3)
        self.assertEquals(sale.margin, 2900)
