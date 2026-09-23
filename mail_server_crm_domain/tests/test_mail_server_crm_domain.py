###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestMailServerCrmDomain(TransactionCase):

    def setUp(self):
        super().setUp()
        self.sale_installed = self.env['ir.module.module'].search([
            ('name', '=', 'sale'),
            ('state', '=', 'installed'),
        ])
        self.sale_stock_installed = self.env['ir.module.module'].search([
            ('name', '=', 'sale_stock'),
            ('state', '=', 'installed'),
        ])
        self.account_installed = self.env['ir.module.module'].search([
            ('name', '=', 'account'),
            ('state', '=', 'installed'),
        ])
        self.test_user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'testuser',
            'email': 'testuser@otherdomain.com',
        })
        self.test_user_not_allowed = self.env['res.users'].create({
            'name': 'Test User Not Allowed',
            'login': 'testuser_not_allowed',
            'email': 'testuser@notallowed.com',
        })
        self.test_partner = self.env['res.partner'].create({
            'name': 'Test Customer',
            'email': 'customer@example.com',
        })
        self.crm_team = self.env['crm.team'].create({
            'name': 'Test Sales Team',
            'mail_domain': 'newdomain.com',
        })
        self.crm_team2 = self.env['crm.team'].create({
            'name': 'Test Sales Team 2',
            'mail_domain': 'otherdomain.com',
        })

    def test_sale_order_email_not_allowed_domain(self):
        if not self.sale_installed:
            self.skipTest('sale module not installed')
        sale_order = self.env['sale.order'].create({
            'partner_id': self.test_partner.id,
            'team_id': self.crm_team.id,
        })
        composer = self.env['mail.compose.message'].with_user(
            self.test_user_not_allowed).create({
                'model': 'sale.order',
                'res_id': sale_order.id,
                'subject': 'Test Sale Order',
                'body': 'Test body',
                'partner_ids': [(4, self.test_partner.id)],
            })
        composer.action_send_mail()
        message = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
        ], order='id desc', limit=1)
        self.assertTrue(message)
        self.assertIn('@notallowed.com', message.email_from)
        self.assertTrue(message.reply_to)
        self.assertIn('@notallowed.com', message.reply_to)

    def test_sale_order_email_domain_replacement(self):
        if not self.sale_installed:
            self.skipTest('sale module not installed')
        sale_order = self.env['sale.order'].create({
            'partner_id': self.test_partner.id,
            'team_id': self.crm_team.id,
        })
        composer = self.env['mail.compose.message'].with_user(
            self.test_user).create({
                'model': 'sale.order',
                'res_id': sale_order.id,
                'subject': 'Test Sale Order',
                'body': 'Test body',
                'partner_ids': [(4, self.test_partner.id)],
            })
        composer.action_send_mail()
        message = self.env['mail.message'].search([
            ('model', '=', 'sale.order'),
        ], order='id desc', limit=1)
        self.assertTrue(message)
        self.assertIn('@newdomain.com', message.email_from)
        self.assertTrue(message.reply_to)
        self.assertIn('@newdomain.com', message.reply_to)

    def test_account_move_email_domain_replacement(self):
        if not self.account_installed:
            self.skipTest('account module not installed')
        account_move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.test_partner.id,
            'team_id': self.crm_team.id,
        })
        composer = self.env['mail.compose.message'].with_user(
            self.test_user).create({
                'model': 'account.move',
                'res_id': account_move.id,
                'subject': 'Test Invoice',
                'body': 'Test body',
                'partner_ids': [(4, self.test_partner.id)],
            })
        composer.action_send_mail()
        message = self.env['mail.message'].search([
            ('model', '=', 'account.move'),
        ], order='id desc', limit=1)
        self.assertTrue(message)
        self.assertIn('@newdomain.com', message.email_from)
        self.assertTrue(message.reply_to)
        self.assertIn('@newdomain.com', message.reply_to)

    def test_stock_picking_email_domain_replacement(self):
        if not self.sale_stock_installed:
            self.skipTest('sale_stock module not installed')
        stock_product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'product',
        })
        sale_order = self.env['sale.order'].create({
            'partner_id': self.test_partner.id,
            'team_id': self.crm_team.id,
            'order_line': [(0, 0, {
                'product_id': stock_product.id,
                'product_uom_qty': 1,
                'price_unit': 10,
            })],
        })
        sale_order.action_confirm()
        stock_picking = sale_order.picking_ids[0]
        composer = self.env['mail.compose.message'].with_user(
            self.test_user).create({
                'model': 'stock.picking',
                'res_id': stock_picking.id,
                'subject': 'Test Delivery Order',
                'body': 'Test body',
                'partner_ids': [(4, self.test_partner.id)],
            })
        composer.action_send_mail()
        message = self.env['mail.message'].search([
            ('model', '=', 'stock.picking'),
        ], order='id desc', limit=1)
        self.assertTrue(message)
        self.assertIn('@newdomain.com', message.email_from)
        self.assertTrue(message.reply_to)
        self.assertIn('@newdomain.com', message.reply_to)
