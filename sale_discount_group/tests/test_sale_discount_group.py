###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import timedelta

from odoo import fields
from odoo.tests import common
from odoo.tests.common import Form


class TestSaleDiscountGroup(common.TransactionCase):

    def setUp(self):
        super().setUp()
        discount_group = self.env.ref('product.group_discount_per_so_line')
        self.env.user.write({'groups_id': [(4, discount_group.id)]})
        self.product = self.env['product.product'].create({
            'name': 'Grouped product',
            'type': 'consu',
            'list_price': 120.0,
        })
        self.product_without_group = self.env['product.product'].create({
            'name': 'Ungrouped product',
            'type': 'consu',
            'list_price': 80.0,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Partner with group',
        })
        self.pricelist = self.partner.property_product_pricelist
        self.pricelist.discount_policy = 'with_discount'
        self.now = fields.Datetime.now()
        self.product_group = self.env['discount.product.group'].create({
            'name': 'Product group',
            'company_id': self.env.company.id,
        })
        self.partner_group = self.env['discount.partner.group'].create({
            'name': 'Partner group',
            'company_id': self.env.company.id,
        })
        self.product.product_tmpl_id.dto_group_id = self.product_group
        self.partner.dto_group_id = self.partner_group
        self.discount_group = self.env['discount.group'].create({
            'name': 'Main discount group',
            'company_id': self.env.company.id,
            'date_start': self.now - timedelta(days=1),
            'date_end': self.now + timedelta(days=1),
            'discount': 10.0,
            'partner_id': self.partner_group.id,
            'product_id': self.product_group.id,
        })

    def _create_order_with_line(
            self, partner=None, pricelist=None, product=None, date_order=False):
        partner = partner or self.partner
        pricelist = pricelist or self.pricelist
        product = product or self.product
        order_vals = {
            'partner_id': partner.id,
            'pricelist_id': pricelist.id,
        }
        if date_order:
            order_vals['date_order'] = date_order
        order = self.env['sale.order'].create(order_vals)
        with Form(order) as order_form:
            with order_form.order_line.new() as line:
                line.product_id = product
                line.product_uom_qty = 1.0
        return order

    def test_product_without_discount_groups(self):
        partner = self.env['res.partner'].create({
            'name': 'Partner without group',
        })
        order = self._create_order_with_line(
            partner=partner, product=self.product_without_group)
        line = order.order_line[:1]
        self.assertFalse(partner.dto_group_id)
        self.assertFalse(self.product_without_group.dto_group_id)
        self.assertEqual(line.discount, 0.0)

    def test_product_with_matching_discount_groups(self):
        order = self._create_order_with_line()
        line = order.order_line[:1]
        self.assertEqual(line.discount, self.discount_group.discount)

    def test_product_with_matching_discount_groups_on_orm_create(self):
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.pricelist.id,
        })
        line = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product.id,
            'product_uom_qty': 1.0,
        })
        self.assertEqual(line.discount, self.discount_group.discount)

    def test_discount_group_not_applied_if_pricelist_rule_disables_it(self):
        pricelist = self.env['product.pricelist'].create({
            'name': 'No discount group pricelist',
        })
        self.env['product.pricelist.item'].create({
            'pricelist_id': pricelist.id,
            'applied_on': '0_product_variant',
            'product_id': self.product.id,
            'compute_price': 'fixed',
            'fixed_price': 70.0,
            'apply_discount_group': False,
        })
        order = self._create_order_with_line(pricelist=pricelist)
        line = order.order_line[:1]
        self.assertEqual(line.discount, 0.0)

    def test_expired_discount_group_not_applied(self):
        self.discount_group.date_end = self.now - timedelta(days=1)
        order = self._create_order_with_line(date_order=self.now)
        line = order.order_line[:1]
        self.assertEqual(line.discount, 0.0)

    def test_discount_is_cleared_when_product_changes(self):
        order = self._create_order_with_line()
        line = order.order_line[:1]
        self.assertEqual(line.discount, self.discount_group.discount)
        with Form(order) as order_form:
            with order_form.order_line.edit(0) as form_line:
                form_line.product_id = self.product_without_group
        order.invalidate_model()
        line = order.order_line[:1]
        self.assertEqual(line.product_id, self.product_without_group)
        self.assertEqual(line.discount, 0.0)

    def test_product_with_discount_group_no_partner_group(self):
        partner = self.env['res.partner'].create({
            'name': 'Partner without dto group',
        })
        order = self._create_order_with_line(partner=partner)
        line = order.order_line[:1]
        self.assertEqual(line.discount, 0.0)

    def test_partner_group_shows_existing_partners(self):
        second_partner = self.env['res.partner'].create({
            'name': 'Second partner',
        })
        second_partner.dto_group_id = self.partner_group
        self.partner_group.invalidate_recordset(['partner_ids'])
        self.assertEqual(
            self.partner_group.partner_ids, self.partner | second_partner)
        second_partner.dto_group_id = False
        self.partner_group.invalidate_recordset(['partner_ids'])
        self.assertEqual(
            self.partner_group.partner_ids, self.partner)

    def test_product_group_shows_existing_products(self):
        second_product = self.env['product.product'].create({
            'name': 'Second product',
            'type': 'consu',
            'list_price': 90.0,
        })
        second_product.product_tmpl_id.dto_group_id = self.product_group
        self.product_group.invalidate_recordset(['product_ids'])
        self.assertEqual(
            self.product_group.product_ids,
            self.product.product_tmpl_id | second_product.product_tmpl_id)
        second_product.product_tmpl_id.dto_group_id = False
        self.product_group.invalidate_recordset(['product_ids'])
        self.assertEqual(
            self.product_group.product_ids, self.product.product_tmpl_id)
