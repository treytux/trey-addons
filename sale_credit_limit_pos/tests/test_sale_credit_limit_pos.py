# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import _
from openerp.tests import common
from openerp.exceptions import Warning as UserError


class SaleCreditLimitPos(common.TransactionCase):

    def setUp(self):
        super(SaleCreditLimitPos, self).setUp()
        self.pos_order_obj = self.env['pos.order']
        self.pos_order_line_obj = self.env['pos.order.line']
        self.partner_obj = self.env['res.partner']
        self.product_obj = self.env['product.product']
        self.user_obj = self.env['res.users']
        self.partner_user_01 = self.partner_obj.create({
            'name': 'User 01',
            'email': 'user_01@test.com',
        })
        self.user_allow = self.user_obj.create({
            'partner_id': self.partner_user_01.id,
            'company_id': self.ref('base.main_company'),
            'name': 'User 01',
            'login': 'user_01',
            'password': 'user_01',
            'groups_id': [(6, 0, [
                self.ref('base.group_user'),
                self.ref('base.group_partner_manager'),
                self.ref('base.group_sale_manager'),
                self.ref('point_of_sale.group_pos_manager'),
                self.ref(
                    'sale_credit_limit.group_view_allow_sell_credit_limit')
            ])],
        })
        self.partner_user_02 = self.partner_obj.create({
            'name': 'User 02',
            'email': 'user_02@test.com',
        })
        self.user_not_allow = self.user_obj.create({
            'partner_id': self.partner_user_02.id,
            'company_id': self.ref('base.main_company'),
            'name': 'User 02',
            'login': 'user_02',
            'password': 'user_02',
            'groups_id': [(6, 0, [
                self.ref('base.group_user'),
                self.ref('base.group_partner_manager'),
                self.ref('base.group_sale_manager'),
                self.ref('point_of_sale.group_pos_manager'),
            ])],
        })
        self.partner_01 = self.partner_obj.create({
            'name': 'Customer 01',
            'is_company': True,
            'customer': True,
            'credit_limit': 20,
        })
        self.partner_02 = self.partner_obj.create({
            'name': 'Customer 02',
            'is_company': True,
            'customer': True,
            'credit_limit': 0,
        })
        self.product_01 = self.product_obj.create({
            'name': 'Test product 01',
            'type': 'product',
            'list_price': 10.50,
        })

    def open_session(self, user):
        config = self.env['pos.config'].sudo(user.id).create({
            'name': 'PointOfSale',
        })
        session = self.env['pos.session'].sudo(user.id).create({
            'user_id': user.id,
            'name': user.name,
            'config_id': config.id,
        })
        session.open_cb()
        return session

    def test_pos_without_permission_blocking(self):
        self.user_not_allow.company_id.credit_limit_type = 'blocking'
        self.assertEqual(
            self.user_not_allow.company_id.credit_limit_type, 'blocking')
        session = self.open_session(self.user_not_allow)
        pos_01 = self.pos_order_obj.sudo(self.user_not_allow.id).create({
            'partner_id': self.partner_01.id,
            'session_id': session.id,
        })
        pos_01.onchange_partner_id(pos_01.partner_id.id)
        line = self.pos_order_line_obj.sudo(self.user_not_allow.id).create({
            'order_id': pos_01.id,
            'product_id': self.product_01.id,
            'qty': 1,
        })
        res = line.onchange_product_id(
            pos_01.pricelist_id.id, line.product_id.id, qty=line.qty)
        line.price_unit = res['value']['price_unit']
        self.assertEquals(line.price_unit, 10.5)
        self.assertIn('9.50', pos_01.info_credit_note)
        self.assertEqual(pos_01.warn_credit_note, '')
        pos_02 = self.pos_order_obj.sudo(self.user_not_allow.id).create({
            'partner_id': self.partner_01.id,
            'session_id': session.id,
        })
        pos_02.onchange_partner_id(pos_02.partner_id.id)
        line = self.pos_order_line_obj.sudo(self.user_not_allow.id).create({
            'order_id': pos_02.id,
            'product_id': self.product_01.id,
            'qty': 2,
        })
        res = line.onchange_product_id(
            pos_02.pricelist_id.id, line.product_id.id, qty=line.qty)
        line.price_unit = res['value']['price_unit']
        self.assertEquals(line.price_unit, 10.5)
        self.assertIn('-1', pos_02.info_credit_note)
        self.assertIn(_(
            'Partner \'Customer 01\' has exceeded the credit limit'),
            pos_02.warn_credit_note)
        self.assertIn(_(
            'are not authorized to confirm the order'),
            pos_02.warn_credit_note)

    def test_pos_without_permission_warning(self):
        self.user_not_allow.company_id.credit_limit_type = 'warning'
        self.assertEqual(
            self.user_not_allow.company_id.credit_limit_type, 'warning')
        session = self.open_session(self.user_not_allow)
        pos_01 = self.pos_order_obj.sudo(self.user_not_allow.id).create({
            'partner_id': self.partner_01.id,
            'session_id': session.id,
        })
        pos_01.onchange_partner_id(pos_01.partner_id.id)
        line = self.pos_order_line_obj.sudo(self.user_not_allow.id).create({
            'order_id': pos_01.id,
            'product_id': self.product_01.id,
            'qty': 1,
        })
        res = line.onchange_product_id(
            pos_01.pricelist_id.id, line.product_id.id, qty=line.qty)
        line.price_unit = res['value']['price_unit']
        self.assertEquals(line.price_unit, 10.5)
        self.assertIn('9.50', pos_01.info_credit_note)
        self.assertEqual(pos_01.warn_credit_note, '')
        pos_02 = self.pos_order_obj.sudo(self.user_not_allow.id).create({
            'partner_id': self.partner_01.id,
            'session_id': session.id,
        })
        pos_02.onchange_partner_id(pos_02.partner_id.id)
        line = self.pos_order_line_obj.sudo(self.user_not_allow.id).create({
            'order_id': pos_02.id,
            'product_id': self.product_01.id,
            'qty': 2,
        })
        res = line.onchange_product_id(
            pos_02.pricelist_id.id, line.product_id.id, qty=line.qty)
        line.price_unit = res['value']['price_unit']
        self.assertEquals(line.price_unit, 10.5)
        self.assertIn('-1', pos_02.info_credit_note)
        self.assertIn(_(
            'Partner \'Customer 01\' has exceeded the credit limit'),
            pos_02.warn_credit_note)
        self.assertNotIn(_(
            'are not authorized to confirm the order'),
            pos_02.warn_credit_note)

    def test_pos_with_permission_blocking(self):
        self.user_allow.company_id.credit_limit_type = 'blocking'
        self.assertEqual(
            self.user_allow.company_id.credit_limit_type, 'blocking')
        session = self.open_session(self.user_allow)
        pos_01 = self.pos_order_obj.sudo(self.user_allow.id).create({
            'partner_id': self.partner_01.id,
            'session_id': session.id,
        })
        pos_01.onchange_partner_id(pos_01.partner_id.id)
        line = self.pos_order_line_obj.sudo(self.user_allow.id).create({
            'order_id': pos_01.id,
            'product_id': self.product_01.id,
            'qty': 1,
        })
        res = line.onchange_product_id(
            pos_01.pricelist_id.id, line.product_id.id, qty=line.qty)
        line.price_unit = res['value']['price_unit']
        self.assertEquals(line.price_unit, 10.5)
        self.assertIn('9.50', pos_01.info_credit_note)
        self.assertEqual(pos_01.warn_credit_note, '')
        pos_02 = self.pos_order_obj.sudo(self.user_allow.id).create({
            'partner_id': self.partner_01.id,
            'session_id': session.id,
        })
        pos_02.onchange_partner_id(pos_02.partner_id.id)
        line = self.pos_order_line_obj.sudo(self.user_allow.id).create({
            'order_id': pos_02.id,
            'product_id': self.product_01.id,
            'qty': 2,
        })
        res = line.onchange_product_id(
            pos_02.pricelist_id.id, line.product_id.id, qty=line.qty)
        line.price_unit = res['value']['price_unit']
        self.assertEquals(line.price_unit, 10.5)
        self.assertIn('-1', pos_02.info_credit_note)
        self.assertIn(_(
            'Partner \'Customer 01\' has exceeded the credit limit'),
            pos_02.warn_credit_note)
        self.assertNotIn(_(
            'are not authorized to confirm the order'),
            pos_02.warn_credit_note)

    def test_pos_with_permission_warning(self):
        self.user_allow.company_id.credit_limit_type = 'warning'
        self.assertEqual(
            self.user_allow.company_id.credit_limit_type, 'warning')
        session = self.open_session(self.user_allow)
        pos_01 = self.pos_order_obj.sudo(self.user_allow.id).create({
            'partner_id': self.partner_01.id,
            'session_id': session.id,
        })
        pos_01.onchange_partner_id(pos_01.partner_id.id)
        line = self.pos_order_line_obj.sudo(self.user_allow.id).create({
            'order_id': pos_01.id,
            'product_id': self.product_01.id,
            'qty': 1,
        })
        res = line.onchange_product_id(
            pos_01.pricelist_id.id, line.product_id.id, qty=line.qty)
        line.price_unit = res['value']['price_unit']
        self.assertEquals(line.price_unit, 10.5)
        self.assertIn('9.50', pos_01.info_credit_note)
        self.assertEqual(pos_01.warn_credit_note, '')
        pos_02 = self.pos_order_obj.sudo(self.user_allow.id).create({
            'partner_id': self.partner_01.id,
            'session_id': session.id,
        })
        pos_02.onchange_partner_id(pos_02.partner_id.id)
        line = self.pos_order_line_obj.sudo(self.user_allow.id).create({
            'order_id': pos_02.id,
            'product_id': self.product_01.id,
            'qty': 2,
        })
        res = line.onchange_product_id(
            pos_02.pricelist_id.id, line.product_id.id, qty=line.qty)
        line.price_unit = res['value']['price_unit']
        self.assertEquals(line.price_unit, 10.5)
        self.assertIn('-1', pos_02.info_credit_note)
        self.assertIn(_(
            'Partner \'Customer 01\' has exceeded the credit limit'),
            pos_02.warn_credit_note)
        self.assertNotIn(_(
            'are not authorized to confirm the order'),
            pos_02.warn_credit_note)

    def test_pos_without_permission_blocking_no_credit_limit(self):
        self.user_not_allow.company_id.credit_limit_type = 'blocking'
        self.assertEqual(
            self.user_not_allow.company_id.credit_limit_type, 'blocking')
        session = self.open_session(self.user_not_allow)
        pos_01 = self.pos_order_obj.sudo(self.user_not_allow.id).create({
            'partner_id': self.partner_02.id,
            'session_id': session.id,
        })
        pos_01.onchange_partner_id(pos_01.partner_id.id)
        line = self.pos_order_line_obj.sudo(self.user_not_allow.id).create({
            'order_id': pos_01.id,
            'product_id': self.product_01.id,
            'qty': 1,
        })
        res = line.onchange_product_id(
            pos_01.pricelist_id.id, line.product_id.id, qty=line.qty)
        line.price_unit = res['value']['price_unit']
        self.assertEquals(line.price_unit, 10.5)
        self.assertEqual(pos_01.info_credit_note, '')
        self.assertEqual(pos_01.warn_credit_note, '')
        pos_02 = self.pos_order_obj.sudo(self.user_not_allow.id).create({
            'partner_id': self.partner_02.id,
            'session_id': session.id,
        })
        pos_02.onchange_partner_id(pos_02.partner_id.id)
        line = self.pos_order_line_obj.sudo(self.user_not_allow.id).create({
            'order_id': pos_02.id,
            'product_id': self.product_01.id,
            'qty': 2,
        })
        res = line.onchange_product_id(
            pos_02.pricelist_id.id, line.product_id.id, qty=line.qty)
        line.price_unit = res['value']['price_unit']
        self.assertEqual(line.price_unit, 10.50)
        self.assertEqual(pos_02.info_credit_note, '')
        self.assertEqual(pos_02.warn_credit_note, '')

    def test_pos_with_permission_warning_no_credit_limit(self):
        self.user_allow.company_id.credit_limit_type = 'warning'
        self.assertEqual(
            self.user_allow.company_id.credit_limit_type, 'warning')
        session = self.open_session(self.user_allow)
        pos_01 = self.pos_order_obj.sudo(self.user_allow.id).create({
            'partner_id': self.partner_02.id,
            'session_id': session.id,
        })
        pos_01.onchange_partner_id(pos_01.partner_id.id)
        line = self.pos_order_line_obj.sudo(self.user_allow.id).create({
            'order_id': pos_01.id,
            'product_id': self.product_01.id,
            'qty': 1,
        })
        res = line.onchange_product_id(
            pos_01.pricelist_id.id, line.product_id.id, qty=line.qty)
        line.price_unit = res['value']['price_unit']
        self.assertEqual(line.price_unit, 10.50)
        self.assertEqual(pos_01.info_credit_note, '')
        self.assertEqual(pos_01.warn_credit_note, '')
        pos_02 = self.pos_order_obj.sudo(self.user_allow.id).create({
            'partner_id': self.partner_02.id,
            'session_id': session.id,
        })
        pos_02.onchange_partner_id(pos_02.partner_id.id)
        line = self.pos_order_line_obj.sudo(self.user_allow.id).create({
            'order_id': pos_02.id,
            'product_id': self.product_01.id,
            'qty': 2,
        })
        res = line.onchange_product_id(
            pos_02.pricelist_id.id, line.product_id.id, qty=line.qty)
        line.price_unit = res['value']['price_unit']
        self.assertEqual(line.price_unit, 10.50)
        self.assertEqual(pos_02.info_credit_note, '')
        self.assertEqual(pos_02.warn_credit_note, '')

    def test_pos_without_permission_blocking_check_payment(self):
        self.user_not_allow.company_id.credit_limit_type = 'blocking'
        self.assertEqual(
            self.user_not_allow.company_id.credit_limit_type, 'blocking')
        session = self.open_session(self.user_not_allow)
        pos_01 = self.pos_order_obj.sudo(self.user_not_allow.id).create({
            'partner_id': self.partner_01.id,
            'session_id': session.id,
        })
        pos_01.onchange_partner_id(pos_01.partner_id.id)
        line = self.pos_order_line_obj.sudo(self.user_not_allow.id).create({
            'order_id': pos_01.id,
            'product_id': self.product_01.id,
            'qty': 1,
        })
        res = line.onchange_product_id(
            pos_01.pricelist_id.id, line.product_id.id, qty=line.qty)
        line.price_unit = res['value']['price_unit']
        self.assertEquals(line.price_unit, 10.5)
        self.assertIn('9.50', pos_01.info_credit_note)
        self.assertEqual(pos_01.warn_credit_note, '')
        wiz = self.env['pos.make.payment'].sudo(
            self.user_not_allow.id).with_context({
                'active_model': 'pos.order',
                'active_id': pos_01.id,
                'active_ids': [pos_01.id],
            }).create({'amount': 10.50})
        wiz.check()
        self.assertEqual(pos_01.state, 'paid')
        pos_02 = self.pos_order_obj.sudo(self.user_not_allow.id).create({
            'partner_id': self.partner_01.id,
            'session_id': session.id,
        })
        pos_02.onchange_partner_id(pos_02.partner_id.id)
        line = self.pos_order_line_obj.sudo(self.user_not_allow.id).create({
            'order_id': pos_02.id,
            'product_id': self.product_01.id,
            'qty': 2,
        })
        res = line.onchange_product_id(
            pos_02.pricelist_id.id, line.product_id.id, qty=line.qty)
        line.price_unit = res['value']['price_unit']
        self.assertEquals(line.price_unit, 10.5)
        self.assertIn('-1', pos_02.info_credit_note)
        self.assertIn(_(
            'Partner \'Customer 01\' has exceeded the credit limit'),
            pos_02.warn_credit_note)
        self.assertIn(_(
            'are not authorized to confirm the order'),
            pos_02.warn_credit_note)
        wiz = self.env['pos.make.payment'].sudo(
            self.user_not_allow.id).with_context({
                'active_model': 'pos.order',
                'active_id': pos_02.id,
                'active_ids': [pos_02.id],
            }).create({'amount': 10.50})
        self.assertRaises(UserError, wiz.sudo(self.user_not_allow.id).check)

    def test_pos_without_permission_warning_check_payment(self):
        self.user_not_allow.company_id.credit_limit_type = 'warning'
        self.assertEqual(
            self.user_not_allow.company_id.credit_limit_type, 'warning')
        session = self.open_session(self.user_not_allow)
        pos_01 = self.pos_order_obj.sudo(self.user_not_allow.id).create({
            'partner_id': self.partner_01.id,
            'session_id': session.id,
        })
        pos_01.onchange_partner_id(pos_01.partner_id.id)
        line = self.pos_order_line_obj.sudo(self.user_not_allow.id).create({
            'order_id': pos_01.id,
            'product_id': self.product_01.id,
            'qty': 1,
        })
        res = line.onchange_product_id(
            pos_01.pricelist_id.id, line.product_id.id, qty=line.qty)
        line.price_unit = res['value']['price_unit']
        self.assertEquals(line.price_unit, 10.5)
        self.assertIn('9.50', pos_01.info_credit_note)
        self.assertEqual(pos_01.warn_credit_note, '')
        wiz = self.env['pos.make.payment'].sudo(
            self.user_not_allow.id).with_context({
                'active_model': 'pos.order',
                'active_id': pos_01.id,
                'active_ids': [pos_01.id],
            }).create({'amount': 10.50})
        wiz.check()
        self.assertEqual(pos_01.state, 'paid')
        pos_02 = self.pos_order_obj.sudo(self.user_not_allow.id).create({
            'partner_id': self.partner_01.id,
            'session_id': session.id,
        })
        pos_02.onchange_partner_id(pos_02.partner_id.id)
        line = self.pos_order_line_obj.sudo(self.user_not_allow.id).create({
            'order_id': pos_02.id,
            'product_id': self.product_01.id,
            'qty': 2,
        })
        res = line.onchange_product_id(
            pos_02.pricelist_id.id, line.product_id.id, qty=line.qty)
        line.price_unit = res['value']['price_unit']
        self.assertEquals(line.price_unit, 10.5)
        self.assertIn('-1', pos_02.info_credit_note)
        self.assertIn(_(
            'Partner \'Customer 01\' has exceeded the credit limit'),
            pos_02.warn_credit_note)
        self.assertNotIn(_(
            'are not authorized to confirm the order'),
            pos_02.warn_credit_note)
        wiz = self.env['pos.make.payment'].sudo(
            self.user_not_allow.id).with_context({
                'active_model': 'pos.order',
                'active_id': pos_02.id,
                'active_ids': [pos_02.id],
            }).create({'amount': 10.50})
        wiz.sudo(self.user_not_allow.id).check()

    def test_pos_with_permission_blocking_check_payment(self):
        self.user_allow.company_id.credit_limit_type = 'blocking'
        self.assertEqual(
            self.user_allow.company_id.credit_limit_type, 'blocking')
        session = self.open_session(self.user_allow)
        pos_01 = self.pos_order_obj.sudo(self.user_allow.id).create({
            'partner_id': self.partner_01.id,
            'session_id': session.id,
        })
        pos_01.onchange_partner_id(pos_01.partner_id.id)
        line = self.pos_order_line_obj.sudo(self.user_allow.id).create({
            'order_id': pos_01.id,
            'product_id': self.product_01.id,
            'qty': 1,
        })
        res = line.onchange_product_id(
            pos_01.pricelist_id.id, line.product_id.id, qty=line.qty)
        line.price_unit = res['value']['price_unit']
        self.assertEquals(line.price_unit, 10.5)
        self.assertIn('9.50', pos_01.info_credit_note)
        self.assertEqual(pos_01.warn_credit_note, '')
        wiz = self.env['pos.make.payment'].sudo(
            self.user_allow.id).with_context({
                'active_model': 'pos.order',
                'active_id': pos_01.id,
                'active_ids': [pos_01.id],
            }).create({'amount': 10.50})
        wiz.check()
        self.assertEqual(pos_01.state, 'paid')
        pos_02 = self.pos_order_obj.sudo(self.user_allow.id).create({
            'partner_id': self.partner_01.id,
            'session_id': session.id,
        })
        pos_02.onchange_partner_id(pos_02.partner_id.id)
        line = self.pos_order_line_obj.sudo(self.user_allow.id).create({
            'order_id': pos_02.id,
            'product_id': self.product_01.id,
            'qty': 2,
        })
        res = line.onchange_product_id(
            pos_02.pricelist_id.id, line.product_id.id, qty=line.qty)
        line.price_unit = res['value']['price_unit']
        self.assertEquals(line.price_unit, 10.5)
        self.assertIn('-1', pos_02.info_credit_note)
        self.assertIn(_(
            'Partner \'Customer 01\' has exceeded the credit limit'),
            pos_02.warn_credit_note)
        wiz = self.env['pos.make.payment'].sudo(
            self.user_allow.id).with_context({
                'active_model': 'pos.order',
                'active_id': pos_02.id,
                'active_ids': [pos_02.id],
            }).create({'amount': 10.50})
        wiz.sudo(self.user_allow.id).check()

    def test_pos_with_permission_warning_check_payment(self):
        self.user_allow.company_id.credit_limit_type = 'warning'
        self.assertEqual(
            self.user_allow.company_id.credit_limit_type, 'warning')
        session = self.open_session(self.user_allow)
        pos_01 = self.pos_order_obj.sudo(self.user_allow.id).create({
            'partner_id': self.partner_01.id,
            'session_id': session.id,
        })
        pos_01.onchange_partner_id(pos_01.partner_id.id)
        line = self.pos_order_line_obj.sudo(self.user_allow.id).create({
            'order_id': pos_01.id,
            'product_id': self.product_01.id,
            'qty': 1,
        })
        res = line.onchange_product_id(
            pos_01.pricelist_id.id, line.product_id.id, qty=line.qty)
        line.price_unit = res['value']['price_unit']
        self.assertEquals(line.price_unit, 10.5)
        self.assertIn('9.50', pos_01.info_credit_note)
        self.assertEqual(pos_01.warn_credit_note, '')
        wiz = self.env['pos.make.payment'].sudo(
            self.user_allow.id).with_context({
                'active_model': 'pos.order',
                'active_id': pos_01.id,
                'active_ids': [pos_01.id],
            }).create({'amount': 10.50})
        wiz.check()
        self.assertEqual(pos_01.state, 'paid')
        pos_02 = self.pos_order_obj.sudo(self.user_allow.id).create({
            'partner_id': self.partner_01.id,
            'session_id': session.id,
        })
        pos_02.onchange_partner_id(pos_02.partner_id.id)
        line = self.pos_order_line_obj.sudo(self.user_allow.id).create({
            'order_id': pos_02.id,
            'product_id': self.product_01.id,
            'qty': 2,
        })
        res = line.onchange_product_id(
            pos_02.pricelist_id.id, line.product_id.id, qty=line.qty)
        line.price_unit = res['value']['price_unit']
        self.assertEquals(line.price_unit, 10.5)
        self.assertIn('-1', pos_02.info_credit_note)
        self.assertIn(_(
            'Partner \'Customer 01\' has exceeded the credit limit'),
            pos_02.warn_credit_note)
        wiz = self.env['pos.make.payment'].sudo(
            self.user_allow.id).with_context({
                'active_model': 'pos.order',
                'active_id': pos_02.id,
                'active_ids': [pos_02.id],
            }).create({'amount': 10.50})
        wiz.sudo(self.user_allow.id).check()
