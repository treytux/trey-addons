###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from dateutil.relativedelta import relativedelta
from odoo import exceptions, fields
from odoo.tests import common


class TestSaleUserLimitMargin(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.ref('base.main_company')
        self.product_01 = self.env['product.product'].create({
            'type': 'product',
            'company_id': self.company.id,
            'name': 'Test product 1',
            'list_price': 10,
            'standard_price': 4,
        })
        self.product_02 = self.env['product.product'].create({
            'type': 'product',
            'company_id': self.company.id,
            'name': 'Test product 2',
            'list_price': 6,
            'standard_price': 4,
        })
        self.customer = self.env['res.partner'].create({
            'name': 'Test customer',
            'email': 'customer@customer.com',
            'customer': True,
        })
        self.customerinfo = self.env['product.customerinfo'].create({
            'name': self.customer.id,
            'product_id': self.product_01.id,
            'product_tmpl_id': self.product_01.product_tmpl_id.id,
            'price': 80.0,
            'discount': 20,
        })
        self.pricelist = self.env['product.pricelist'].create({
            'name': 'Test pricelist',
            'currency_id': self.env.ref('base.EUR').id,
        })
        self.pricelist_item = self.env['product.pricelist.item'].create({
            'applied_on': '1_product',
            'base': 'partner',
            'name': 'Test pricelist item',
            'pricelist_id': self.pricelist.id,
            'compute_price': 'fixed',
            'fixed_price': self.customerinfo.price,
            'product_id': self.product_01.id,
        })
        self.sale_01 = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'company_id': self.company.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_02.id,
                    'product_uom_qty': 1}),
            ]
        })
        self.sale_02 = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'company_id': self.company.id,
            'pricelist_id': self.pricelist.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'discount': 20,
                    'product_uom_qty': 1}),
            ]
        })
        self.user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'user@test.com',
            'email': 'user@test.com',
            'company_ids': [(6, 0, [self.company.id])],
            'company_id': self.company.id,
            'groups_id': [
                (4, self.env.ref('sales_team.group_sale_manager').id),
                (4, self.env.ref('base.group_user').id),
            ],
            'sales_amount_limit': 100,
            'sales_margin_limit': 10,
            'sales_discount_limit': 30,
        })

    def test_sale_user_limit_margin_no_customerinfo_ok(self):
        self.assertFalse(self.env.user.apply_margin_limit)
        self.env.user.apply_margin_limit = True
        self.assertTrue(self.env.user.apply_margin_limit)
        self.assertEquals(self.env.user.sales_amount_limit, 0)
        self.env.user.sales_amount_limit = 100
        self.assertEquals(self.env.user.sales_amount_limit, 100)
        self.assertFalse(self.env.user.sales_margin_limit)
        self.env.user.sales_margin_limit = 20
        self.assertEquals(self.env.user.sales_margin_limit, 20)
        self.assertFalse(
            self.sale_01.search_product_customerinfo(
                self.sale_01.order_line[0]))
        self.assertTrue(self.sale_01.check_order_margin_limits())
        self.sale_01.action_confirm()
        self.assertEquals(self.sale_01.state, 'sale')

    def test_sale_user_limit_margin_no_customerinfo_error_01(self):
        self.assertFalse(self.env.user.apply_margin_limit)
        self.env.user.apply_margin_limit = True
        self.assertTrue(self.env.user.apply_margin_limit)
        self.assertEquals(self.env.user.sales_amount_limit, 0)
        self.env.user.sales_amount_limit = 100
        self.assertEquals(self.env.user.sales_amount_limit, 100)
        self.assertEquals(self.env.user.sales_margin_limit, 0)
        self.env.user.sales_margin_limit = 20
        self.assertEquals(self.env.user.sales_margin_limit, 20)
        self.product_02.standard_price = 5.3
        self.assertEquals(self.product_02.standard_price, 5.3)
        self.assertFalse(
            self.sale_01.search_product_customerinfo(
                self.sale_01.order_line[0]))
        self.assertFalse(self.sale_01.check_order_margin_limits())
        with self.assertRaises(exceptions.ValidationError) as result:
            self.sale_01.action_confirm()
        self.assertEqual(
            result.exception.name,
            'Sales margin limits [%s] exceeded by the user %s' % (
                self.env.user.sales_margin_limit, self.env.user.name))
        self.assertEquals(self.sale_01.state, 'draft')

    def test_sale_user_limit_margin_no_customerinfo_error_other_user_ok(self):
        self.assertFalse(self.env.user.apply_margin_limit)
        self.env.user.apply_margin_limit = True
        self.assertTrue(self.env.user.apply_margin_limit)
        self.assertEquals(self.user.sales_amount_limit, 100)
        self.assertEquals(self.user.sales_margin_limit, 10)
        self.assertEquals(self.env.user.sales_amount_limit, 0)
        self.env.user.sales_amount_limit = 100
        self.assertEquals(self.env.user.sales_amount_limit, 100)
        self.assertEquals(self.env.user.sales_margin_limit, 0)
        self.env.user.sales_margin_limit = 20
        self.assertEquals(self.env.user.sales_margin_limit, 20)
        self.product_02.standard_price = 5.3
        self.assertEquals(self.product_02.standard_price, 5.3)
        self.assertFalse(
            self.sale_01.search_product_customerinfo(
                self.sale_01.order_line[0]))
        self.assertFalse(self.sale_01.check_order_margin_limits())
        with self.assertRaises(exceptions.ValidationError) as result:
            self.sale_01.action_confirm()
        self.assertEqual(
            result.exception.name,
            'Sales margin limits [%s] exceeded by the user %s' % (
                self.env.user.sales_margin_limit, self.env.user.name))
        self.assertEquals(self.sale_01.state, 'draft')
        self.sale_01.sudo(user=self.user).action_confirm()
        self.assertEquals(self.sale_01.state, 'sale')

    def test_sale_user_limit_margin_no_customerinfo_error_02(self):
        self.assertFalse(self.env.user.apply_margin_limit)
        self.env.user.apply_margin_limit = True
        self.assertTrue(self.env.user.apply_margin_limit)
        self.assertEquals(self.env.user.sales_amount_limit, 0)
        self.env.user.sales_amount_limit = 100
        self.assertEquals(self.env.user.sales_amount_limit, 100)
        self.assertEquals(self.env.user.sales_margin_limit, 0)
        self.env.user.sales_margin_limit = 20
        self.assertEquals(self.env.user.sales_margin_limit, 20)
        self.product_02.standard_price = 6.2
        self.assertEquals(self.product_02.standard_price, 6.2)
        self.assertFalse(
            self.sale_01.search_product_customerinfo(
                self.sale_01.order_line[0]))
        self.assertFalse(self.sale_01.check_order_margin_limits())
        with self.assertRaises(exceptions.ValidationError) as result:
            self.sale_01.action_confirm()
        self.assertEqual(
            result.exception.name,
            'Sales margin limits [%s] exceeded by the user %s' % (
                self.env.user.sales_margin_limit, self.env.user.name))
        self.assertEquals(self.sale_01.state, 'draft')

    def test_sale_user_limit_margin_only_line_with_customerinfo(self):
        self.assertFalse(self.env.user.apply_margin_limit)
        self.env.user.apply_margin_limit = True
        self.assertTrue(self.env.user.apply_margin_limit)
        self.assertEquals(self.env.user.sales_amount_limit, 0)
        self.env.user.sales_amount_limit = 100
        self.assertEquals(self.env.user.sales_amount_limit, 100)
        self.assertFalse(self.env.user.sales_margin_limit)
        self.env.user.sales_margin_limit = 20
        self.assertEquals(self.env.user.sales_margin_limit, 20)
        customerinfo = self.sale_02.search_product_customerinfo(
            self.sale_02.order_line[0])
        self.assertEquals(len(customerinfo), 1)
        self.assertEquals(customerinfo, self.customerinfo)
        self.assertTrue(self.sale_02.check_order_margin_limits())
        self.sale_02.action_confirm()
        self.assertEquals(self.sale_02.state, 'pending-approve')

    def test_sale_user_limit_margin_with_customerinfo_ok(self):
        self.sale_02.order_line.create({
            'order_id': self.sale_02.id,
            'product_id': self.product_02.id,
            'price_unit': self.product_02.list_price,
            'product_uom_qty': 1,
        })
        self.assertEquals(self.env.user.sales_amount_limit, 0)
        self.env.user.sales_amount_limit = 100
        self.assertEquals(self.env.user.sales_amount_limit, 100)
        self.assertFalse(self.env.user.sales_margin_limit)
        self.env.user.sales_margin_limit = 20
        self.assertEquals(self.env.user.sales_margin_limit, 20)
        self.assertEquals(self.env.user.sales_discount_limit, 0)
        self.env.user.sales_discount_limit = 30
        self.assertEquals(self.env.user.sales_discount_limit, 30)
        customerinfo = self.sale_02.search_product_customerinfo(
            self.sale_02.order_line[0])
        self.assertEquals(len(customerinfo), 1)
        self.assertEquals(customerinfo, self.customerinfo)
        customerinfo = self.sale_02.search_product_customerinfo(
            self.sale_02.order_line[1])
        self.assertEquals(len(customerinfo), 0)
        self.assertTrue(self.sale_02.check_order_margin_limits())
        self.sale_02.action_confirm()
        self.assertEquals(self.sale_02.state, 'sale')

    def test_sale_user_limit_margin_with_customerinfo_error_all_actions(self):
        self.assertFalse(self.env.user.apply_margin_limit)
        self.env.user.apply_margin_limit = True
        self.assertTrue(self.env.user.apply_margin_limit)
        self.sale_02.order_line.create({
            'order_id': self.sale_02.id,
            'product_id': self.product_02.id,
            'price_unit': self.product_02.list_price,
            'product_uom_qty': 1,
        })
        self.assertEquals(self.env.user.sales_amount_limit, 0)
        self.env.user.sales_amount_limit = 100
        self.assertEquals(self.env.user.sales_amount_limit, 100)
        self.assertFalse(self.env.user.sales_margin_limit)
        self.env.user.sales_margin_limit = 20
        self.assertEquals(self.env.user.sales_margin_limit, 20)
        self.assertEquals(self.env.user.sales_discount_limit, 0)
        self.env.user.sales_discount_limit = 30
        self.assertEquals(self.env.user.sales_discount_limit, 30)
        customerinfo = self.sale_02.search_product_customerinfo(
            self.sale_02.order_line[0])
        self.assertEquals(len(customerinfo), 1)
        self.assertEquals(customerinfo, self.customerinfo)
        customerinfo = self.sale_02.search_product_customerinfo(
            self.sale_02.order_line[1])
        self.assertEquals(len(customerinfo), 0)
        self.product_02.standard_price = 5.3
        self.assertEquals(self.product_02.standard_price, 5.3)
        self.assertFalse(self.sale_02.check_order_margin_limits())
        with self.assertRaises(exceptions.ValidationError) as result:
            self.sale_02.action_confirm()
        self.assertEqual(
            result.exception.name,
            'Sales margin limits [%s] exceeded by the user %s' % (
                self.env.user.sales_margin_limit, self.env.user.name))
        self.assertEquals(self.sale_02.state, 'draft')
        with self.assertRaises(exceptions.ValidationError) as result:
            self.sale_02.action_done()
        self.assertEqual(
            result.exception.name,
            'Sales margin limits [%s] exceeded by the user %s' % (
                self.env.user.sales_margin_limit, self.env.user.name))
        self.assertEquals(self.sale_02.state, 'draft')
        with self.assertRaises(exceptions.ValidationError) as result:
            self.sale_02.action_quotation_send()
        self.assertEqual(
            result.exception.name,
            'Sales margin limits [%s] exceeded by the user %s' % (
                self.env.user.sales_margin_limit, self.env.user.name))
        self.assertEquals(self.sale_02.state, 'draft')
        with self.assertRaises(exceptions.ValidationError) as result:
            self.sale_02.print_quotation()
        self.assertEqual(
            result.exception.name,
            'Sales margin limits [%s] exceeded by the user %s' % (
                self.env.user.sales_margin_limit, self.env.user.name))
        self.assertEquals(self.sale_02.state, 'draft')
        with self.assertRaises(exceptions.ValidationError) as result:
            self.sale_02.preview_sale_order()
        self.assertEqual(
            result.exception.name,
            'Sales margin limits [%s] exceeded by the user %s' % (
                self.env.user.sales_margin_limit, self.env.user.name))
        self.assertEquals(self.sale_02.state, 'draft')

    def test_sale_user_limit_margin_error_confirm_other_user(self):
        self.assertFalse(self.env.user.apply_margin_limit)
        self.env.user.apply_margin_limit = True
        self.assertTrue(self.env.user.apply_margin_limit)
        self.assertEquals(self.user.sales_amount_limit, 100)
        self.assertEquals(self.user.sales_margin_limit, 10)
        self.assertEquals(self.user.sales_discount_limit, 30)
        self.sale_02.order_line.create({
            'order_id': self.sale_02.id,
            'product_id': self.product_02.id,
            'price_unit': self.product_02.list_price,
            'product_uom_qty': 1,
        })
        self.assertEquals(self.env.user.sales_amount_limit, 0)
        self.env.user.sales_amount_limit = 100
        self.assertEquals(self.env.user.sales_amount_limit, 100)
        self.assertFalse(self.env.user.sales_margin_limit)
        self.env.user.sales_margin_limit = 20
        self.assertEquals(self.env.user.sales_margin_limit, 20)
        self.assertEquals(self.env.user.sales_discount_limit, 0)
        self.env.user.sales_discount_limit = 30
        self.assertEquals(self.env.user.sales_discount_limit, 30)
        customerinfo = self.sale_02.search_product_customerinfo(
            self.sale_02.order_line[0])
        self.assertEquals(len(customerinfo), 1)
        self.assertEquals(customerinfo, self.customerinfo)
        customerinfo = self.sale_02.search_product_customerinfo(
            self.sale_02.order_line[1])
        self.assertEquals(len(customerinfo), 0)
        self.product_02.standard_price = 5.3
        self.assertEquals(self.product_02.standard_price, 5.3)
        self.assertFalse(self.sale_02.check_order_margin_limits())
        with self.assertRaises(exceptions.ValidationError) as result:
            self.sale_02.action_confirm()
        self.assertEqual(
            result.exception.name,
            'Sales margin limits [%s] exceeded by the user %s' % (
                self.env.user.sales_margin_limit, self.env.user.name))
        self.assertEquals(self.sale_02.state, 'draft')
        self.sale_02.sudo(user=self.user).action_confirm()
        self.assertEquals(self.sale_02.state, 'sale')

    def test_sale_user_limit_margin_check_valid_date(self):
        self.sale_02.order_line.create({
            'order_id': self.sale_02.id,
            'product_id': self.product_02.id,
            'product_uom_qty': 1,
        })
        self.assertEquals(self.env.user.sales_amount_limit, 0)
        self.env.user.sales_amount_limit = 100
        self.assertEquals(self.env.user.sales_amount_limit, 100)
        self.assertFalse(self.env.user.sales_margin_limit)
        self.env.user.sales_margin_limit = 20
        self.assertEquals(self.env.user.sales_margin_limit, 20)
        self.assertEquals(self.env.user.sales_discount_limit, 0)
        self.env.user.sales_discount_limit = 30
        self.assertEquals(self.env.user.sales_discount_limit, 30)
        self.customerinfo.date_start = (
            fields.Date.today() - relativedelta(days=3))
        self.customerinfo.date_end = (
            fields.Date.today() - relativedelta(days=1))
        customerinfo = self.sale_02.search_product_customerinfo(
            self.sale_02.order_line[0])
        self.assertEquals(len(customerinfo), 0)
        customerinfo = self.sale_02.search_product_customerinfo(
            self.sale_02.order_line[1])
        self.assertEquals(len(customerinfo), 0)

    def test_sale_user_limit_margin_check_min_qty(self):
        self.sale_02.order_line.create({
            'order_id': self.sale_02.id,
            'product_id': self.product_02.id,
            'product_uom_qty': 1,
        })
        self.assertEquals(self.env.user.sales_amount_limit, 0)
        self.env.user.sales_amount_limit = 100
        self.assertEquals(self.env.user.sales_amount_limit, 100)
        self.assertFalse(self.env.user.sales_margin_limit)
        self.env.user.sales_margin_limit = 20
        self.assertEquals(self.env.user.sales_margin_limit, 20)
        self.assertEquals(self.env.user.sales_discount_limit, 0)
        self.env.user.sales_discount_limit = 30
        self.assertEquals(self.env.user.sales_discount_limit, 30)
        self.customerinfo.min_qty = 3
        self.assertEquals(self.customerinfo.min_qty, 3)
        customerinfo = self.sale_02.search_product_customerinfo(
            self.sale_02.order_line[0])
        self.assertEquals(len(customerinfo), 0)
        customerinfo = self.sale_02.search_product_customerinfo(
            self.sale_02.order_line[1])
        self.assertEquals(len(customerinfo), 0)

    def test_action_request_permission_exceed_limit(self):
        self.assertTrue(self.sale_01.user_id)
        self.assertFalse(self.env.user.apply_margin_limit)
        self.env.user.apply_margin_limit = True
        self.assertTrue(self.env.user.apply_margin_limit)
        self.assertEquals(self.env.user.sales_amount_limit, 0)
        self.env.user.sales_amount_limit = 100
        self.assertEquals(self.env.user.sales_amount_limit, 100)
        self.assertEquals(self.env.user.sales_margin_limit, 0)
        self.env.user.sales_margin_limit = 20
        self.assertEquals(self.env.user.sales_margin_limit, 20)
        self.product_02.standard_price = 5.3
        self.assertEquals(self.product_02.standard_price, 5.3)
        self.assertFalse(
            self.sale_01.search_product_customerinfo(
                self.sale_01.order_line[0]))
        self.assertFalse(self.sale_01.check_order_margin_limits())
        comments = len(self.sale_01.message_ids)
        self.sale_01.action_request_permission()
        self.assertEquals(comments + 2, len(self.sale_01.message_ids))
        msg = (
            'An email has been sent to salesperson %s for review and confirm '
            'this sale order') % (self.sale_01.user_id)
        self.assertIn(msg, self.sale_01.message_ids[0].body)

    def test_action_request_permission_no_exceed_limit(self):
        self.assertTrue(self.sale_01.user_id)
        self.assertFalse(self.env.user.apply_margin_limit)
        self.env.user.apply_margin_limit = True
        self.assertTrue(self.env.user.apply_margin_limit)
        self.assertEquals(self.env.user.sales_amount_limit, 0)
        self.env.user.sales_amount_limit = 100
        self.assertEquals(self.env.user.sales_amount_limit, 100)
        self.assertFalse(self.env.user.sales_margin_limit)
        self.env.user.sales_margin_limit = 20
        self.assertEquals(self.env.user.sales_margin_limit, 20)
        self.assertFalse(
            self.sale_01.search_product_customerinfo(
                self.sale_01.order_line[0]))
        comments = len(self.sale_01.message_ids)
        self.sale_01.action_request_permission()
        self.assertEquals(comments, len(self.sale_01.message_ids))

    def test_apply_margin_limit_is_false(self):
        self.assertTrue(self.sale_01.user_id)
        self.assertFalse(self.env.user.apply_margin_limit)
        self.assertEquals(self.env.user.sales_amount_limit, 0)
        self.env.user.sales_amount_limit = 100
        self.assertEquals(self.env.user.sales_amount_limit, 100)
        self.assertEquals(self.env.user.sales_margin_limit, 0)
        self.env.user.sales_margin_limit = 20
        self.assertEquals(self.env.user.sales_margin_limit, 20)
        self.product_02.standard_price = 5.3
        self.assertEquals(self.product_02.standard_price, 5.3)
        self.assertFalse(
            self.sale_01.search_product_customerinfo(
                self.sale_01.order_line[0]))
        comments = len(self.sale_01.message_ids)
        self.sale_01.action_request_permission()
        self.assertEquals(comments, len(self.sale_01.message_ids))

    def test_no_supervisors_assigned_to_user(self):
        self.assertTrue(self.sale_01.user_id)
        self.sale_01.user_id = False
        self.assertFalse(self.sale_01.user_id)
        self.assertFalse(self.env.user.apply_margin_limit)
        self.env.user.apply_margin_limit = True
        self.assertTrue(self.env.user.apply_margin_limit)
        self.assertEquals(self.env.user.sales_amount_limit, 0)
        self.env.user.sales_amount_limit = 100
        self.assertEquals(self.env.user.sales_amount_limit, 100)
        self.assertEquals(self.env.user.sales_margin_limit, 0)
        self.env.user.sales_margin_limit = 20
        self.assertEquals(self.env.user.sales_margin_limit, 20)
        self.product_02.standard_price = 5.3
        self.assertEquals(self.product_02.standard_price, 5.3)
        self.assertFalse(
            self.sale_01.search_product_customerinfo(
                self.sale_01.order_line[0]))
        self.assertFalse(self.sale_01.check_order_margin_limits())
        comments = len(self.sale_01.message_ids)
        with self.assertRaises(exceptions.ValidationError) as result:
            self.sale_01.action_request_permission()
        self.assertEqual(
            result.exception.name,
            'Mail cannot be sent because no salesperson is assigned')
        self.assertEquals(comments, len(self.sale_01.message_ids))
