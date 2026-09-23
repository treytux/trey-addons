###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import timedelta

from odoo import _, fields
from odoo.tests import common


class TestSaleLimitMarginAlert(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.product = self.env['product.product'].create({
            'type': 'consu',
            'company_id': False,
            'name': 'Product test',
            'standard_price': 10,
            'list_price': 30,
            'default_code': 'TEST-1',
        })
        self.user = self.env.ref('base.user_admin')
        self.team = self.env['crm.team'].create({
            'name': 'Team test',
            'user_id': self.user.id,
        })
        self.company = self.env.ref('base.main_company')
        self.sale = self.env['sale.order'].create({
            'company_id': self.company.id,
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 25,
                    'product_uom_qty': 1,
                })
            ]
        })
        self.company.margin_limit = 10.0
        self.res_model_id = self.env['ir.model']._get('sale.order')

    def test_sale_lines_margin_ok(self):
        self.assertEqual(self.sale.state, 'draft')
        self.assertEqual(self.company.margin_limit, 10.0)
        self.assertFalse(self.sale.order_line[0].is_delivery)
        self.assertFalse(self.company.include_delivery_lines)
        activities_01 = self.env['mail.activity'].search([
            ('res_id', '=', self.sale.id),
            ('res_model_id', '=', self.res_model_id.id),
        ])
        self.sale.action_confirm()
        activities_02 = self.env['mail.activity'].search([
            ('res_id', '=', self.sale.id),
            ('res_model_id', '=', self.res_model_id.id),
        ])
        self.assertEqual(len(activities_01), len(activities_02))

    def test_sale_lines_margin_exceeded(self):
        self.assertEqual(self.sale.state, 'draft')
        self.assertEqual(self.company.margin_limit, 10.0)
        self.assertFalse(self.company.include_delivery_lines)
        self.assertFalse(self.sale.order_line[0].is_delivery)
        self.assertEqual(self.sale.team_id, self.team)
        self.sale.order_line[0].price_unit = 10
        activities_01 = self.env['mail.activity'].search([
            ('res_id', '=', self.sale.id),
            ('res_model_id', '=', self.res_model_id.id),
        ])
        self.sale.action_confirm()
        activities_02 = self.env['mail.activity'].search([
            ('res_id', '=', self.sale.id),
            ('res_model_id', '=', self.res_model_id.id),
        ])
        self.assertNotEqual(len(activities_01), len(activities_02))
        self.assertEqual(len(activities_01), 0)
        self.assertEqual(len(activities_02), 1)
        activity = activities_02[0]
        self.assertEqual(
            activity.activity_type_id,
            self.env.ref('mail.mail_activity_data_warning'))
        self.assertEqual(activity.res_id, self.sale.id)
        self.assertEqual(activity.user_id, self.user)
        self.assertEqual(
            activity.date_deadline, fields.Date.today() + timedelta(days=7))
        self.assertIn(_('Margin limit alert on sales order'), activity.summary)

    def test_sale_margin_ok_include_delivery_lines_true(self):
        self.assertEqual(self.sale.state, 'draft')
        self.assertEqual(self.company.margin_limit, 10.0)
        self.assertFalse(self.sale.order_line[0].is_delivery)
        self.sale.order_line[0].is_delivery = True
        self.assertTrue(self.sale.order_line[0].is_delivery)
        self.assertFalse(self.company.include_delivery_lines)
        self.company.include_delivery_lines = True
        self.assertTrue(self.company.include_delivery_lines)
        activities_01 = self.env['mail.activity'].search([
            ('res_id', '=', self.sale.id),
            ('res_model_id', '=', self.res_model_id.id),
        ])
        self.sale.action_confirm()
        activities_02 = self.env['mail.activity'].search([
            ('res_id', '=', self.sale.id),
            ('res_model_id', '=', self.res_model_id.id),
        ])
        self.assertEqual(len(activities_01), len(activities_02))

    def test_sale_margin_error_include_delivery_lines_true(self):
        self.assertEqual(self.sale.state, 'draft')
        self.assertEqual(self.company.margin_limit, 10.0)
        self.assertEqual(self.sale.team_id, self.team)
        self.sale.order_line[0].price_unit = 10
        self.assertFalse(self.sale.order_line[0].is_delivery)
        self.sale.order_line[0].is_delivery = True
        self.assertTrue(self.sale.order_line[0].is_delivery)
        self.assertFalse(self.company.include_delivery_lines)
        self.company.include_delivery_lines = True
        self.assertTrue(self.company.include_delivery_lines)
        activities_01 = self.env['mail.activity'].search([
            ('res_id', '=', self.sale.id),
            ('res_model_id', '=', self.res_model_id.id),
        ])
        self.sale.action_confirm()
        activities_02 = self.env['mail.activity'].search([
            ('res_id', '=', self.sale.id),
            ('res_model_id', '=', self.res_model_id.id),
        ])
        self.assertNotEqual(len(activities_01), len(activities_02))
        self.assertEqual(len(activities_01), 0)
        self.assertEqual(len(activities_02), 1)
        activity = activities_02[0]
        self.assertEqual(
            activity.activity_type_id,
            self.env.ref('mail.mail_activity_data_warning'))
        self.assertEqual(activity.res_id, self.sale.id)
        self.assertEqual(activity.user_id, self.user)
        self.assertEqual(
            activity.date_deadline, fields.Date.today() + timedelta(days=7))
        self.assertIn(_('Margin limit alert on sales order'), activity.summary)

    def test_sale_margin_exceeded_notify_sales_team_manager(self):
        self.assertEqual(self.sale.state, 'draft')
        self.assertEqual(self.company.margin_limit, 10.0)
        self.assertEqual(self.sale.team_id, self.team)
        self.assertTrue(self.sale.team_id.user_id)
        self.sale.order_line[0].price_unit = 10
        self.assertEqual(self.company.notification_method, 'team_manager')
        activities_01 = self.env['mail.activity'].search([
            ('res_id', '=', self.sale.id),
            ('res_model_id', '=', self.res_model_id.id),
        ])
        self.sale.action_confirm()
        activities_02 = self.env['mail.activity'].search([
            ('res_id', '=', self.sale.id),
            ('res_model_id', '=', self.res_model_id.id),
        ])
        self.assertNotEqual(len(activities_01), len(activities_02))
        self.assertEqual(len(activities_01), 0)
        self.assertEqual(len(activities_02), 1)
        activity = activities_02[0]
        self.assertEqual(
            activity.activity_type_id,
            self.env.ref('mail.mail_activity_data_warning'))
        self.assertEqual(activity.user_id, self.team.user_id)
        self.assertIn(_('Margin limit alert on sales order'), activity.summary)

    def test_sale_margin_exceeded_notify_user_company_config(self):
        self.assertEqual(self.sale.state, 'draft')
        self.assertEqual(self.company.margin_limit, 10.0)
        self.company.notification_method = 'user_unique'
        self.assertEqual(self.company.notification_method, 'user_unique')
        self.company.notification_user = self.user.id
        self.assertEqual(self.company.notification_user, self.user)
        self.sale.order_line[0].price_unit = 10
        activities_01 = self.env['mail.activity'].search([
            ('res_id', '=', self.sale.id),
            ('res_model_id', '=', self.res_model_id.id),
        ])
        self.sale.action_confirm()
        activities_02 = self.env['mail.activity'].search([
            ('res_id', '=', self.sale.id),
            ('res_model_id', '=', self.res_model_id.id),
        ])
        self.assertNotEqual(len(activities_01), len(activities_02))
        self.assertEqual(len(activities_01), 0)
        self.assertEqual(len(activities_02), 1)
        activity = activities_02[0]
        self.assertEqual(
            activity.activity_type_id,
            self.env.ref('mail.mail_activity_data_warning'))
        self.assertEqual(activity.user_id, self.company.notification_user)
        self.assertIn(_('Margin limit alert on sales order'), activity.summary)

    def test_sale_lines_margin_ok_discount(self):
        self.assertEqual(self.sale.state, 'draft')
        self.assertEqual(self.company.margin_limit, 10.0)
        activities_01 = self.env['mail.activity'].search([
            ('res_id', '=', self.sale.id),
            ('res_model_id', '=', self.res_model_id.id),
        ])
        self.sale.order_line[0].discount = 50
        self.assertEqual(self.sale.order_line[0].discount, 50)
        self.sale.action_confirm()
        activities_02 = self.env['mail.activity'].search([
            ('res_id', '=', self.sale.id),
            ('res_model_id', '=', self.res_model_id.id),
        ])
        self.assertEqual(len(activities_01), len(activities_02))

    def test_sale_lines_margin_exceeded_discount(self):
        self.assertEqual(self.sale.state, 'draft')
        self.assertEqual(self.company.margin_limit, 10.0)
        activities_01 = self.env['mail.activity'].search([
            ('res_id', '=', self.sale.id),
            ('res_model_id', '=', self.res_model_id.id),
        ])
        self.sale.order_line[0].discount = 65
        self.assertEqual(self.sale.order_line[0].discount, 65)
        self.sale.action_confirm()
        activities_02 = self.env['mail.activity'].search([
            ('res_id', '=', self.sale.id),
            ('res_model_id', '=', self.res_model_id.id),
        ])
        self.assertNotEqual(len(activities_01), len(activities_02))
        self.assertEqual(len(activities_01), 0)
        self.assertEqual(len(activities_02), 1)
        activity = activities_02[0]
        self.assertEqual(
            activity.activity_type_id,
            self.env.ref('mail.mail_activity_data_warning'))
        self.assertIn(_('Margin limit alert on sales order'), activity.summary)

    def test_not_user_id_crm_team(self):
        self.assertEqual(self.sale.state, 'draft')
        self.assertEqual(self.company.margin_limit, 10.0)
        self.assertTrue(self.sale.team_id.user_id)
        self.team.user_id = False
        self.assertFalse(self.sale.team_id.user_id)
        self.sale.order_line[0].price_unit = 10
        self.company.notification_user = self.user.id
        activities_01 = self.env['mail.activity'].search([
            ('res_id', '=', self.sale.id),
            ('res_model_id', '=', self.res_model_id.id),
        ])
        self.sale.action_confirm()
        activities_02 = self.env['mail.activity'].search([
            ('res_id', '=', self.sale.id),
            ('res_model_id', '=', self.res_model_id.id),
        ])
        self.assertNotEqual(len(activities_01), len(activities_02))
        self.assertEqual(len(activities_01), 0)
        self.assertEqual(len(activities_02), 1)
        activity = activities_02[0]
        self.assertEqual(
            activity.activity_type_id,
            self.env.ref('mail.mail_activity_data_warning'))
        self.assertEqual(activity.user_id, self.user)
        self.assertIn(_('Margin limit alert on sales order'), activity.summary)
