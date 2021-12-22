###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.tests import common


class TestStockPickingAssign(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env['res.company'].create({
            'name': 'Company test',
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': False,
        })
        self.product = self.env['product.product'].create({
            'type': 'consu',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'price_unit': 15,
                }),
            ],
        })
        self.external_user = self.env['res.users'].create({
            'name': 'Test user',
            'login': 'user@test.com',
            'company_ids': [(6, 0, [self.company.id])],
            'company_id': self.company.id,
            'groups_id': [(6, 0, [
                self.env.ref('base.group_no_one').id,
            ])],
        })
        self.internal_user = self.env['res.users'].create({
            'name': 'Internal user',
            'login': 'internal@user.com',
            'company_ids': [(6, 0, [self.company.id])],
            'company_id': self.company.id,
            'groups_id': [(6, 0, [
                self.env.ref('base.group_no_one').id,
            ])],
            'share': False,
        })

    def test_assigned_internal_user_stock_picking(self):
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        self.assertFalse(picking.assign_id)
        picking.assign_stock_picking_to_user()
        self.assertTrue(picking.assign_id)
        self.assertEqual(self.env.user, picking.assign_id)

    def test_error_try_assigned_not_internal_user_stock_picking(self):
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        self.assertTrue(self.external_user.share)
        picking = self.sale.picking_ids[0]
        self.assertFalse(picking.assign_id)
        with self.assertRaises(exceptions.ValidationError) as result:
            picking.assign_id = self.external_user.id
        self.assertEqual(
            result.exception.name, 'The user has to be of internal type')
