###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _
from odoo.tests.common import TransactionCase


class TestAccountInvoiceWithoutEmailFollowers(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'email': 'test@test.es',
        })
        self.partner2 = self.env['res.partner'].create({
            'name': 'Partner2 test',
            'email': 'test2@test.es',
        })
        self.partner_without_mail = self.env['res.partner'].create({
            'name': 'Partner test without mail',
        })
        self.partner_without_mail2 = self.env['res.partner'].create({
            'name': 'Partner test without mail 2',
        })
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.journal = self.env['account.journal'].search([
            ('company_id', '=', self.env.user.company_id.id),
            ('type', '=', 'sale')], limit=1)
        self.account = self.env.user.company_id.get_chart_of_accounts_or_fail()

    def test_partner_without_mail_follower_without_mail(self):
        invoice = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner_without_mail.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'account_id': self.account.id,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        invoice2 = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner_without_mail2.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'account_id': self.account.id,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        self.env['mail.followers'].sudo().search([
            ('res_model', '=', 'account.invoice'),
            ('res_id', '=', invoice2.id),
            ('partner_id', '=', self.env.user.partner_id.id),
        ]).unlink()
        self.env['mail.followers'].sudo().search([
            ('res_model', '=', 'account.invoice'),
            ('res_id', '=', invoice.id),
            ('partner_id', '=', self.env.user.partner_id.id),
        ]).unlink()
        self.env['mail.followers'].create({
            'res_model': 'account.invoice',
            'res_id': invoice.id,
            'partner_id': self.partner_without_mail2.id,
        })
        self.env['mail.followers'].create({
            'res_model': 'account.invoice',
            'res_id': invoice.id,
            'partner_id': self.partner_without_mail.id,
        })
        self.env['mail.followers'].create({
            'res_model': 'account.invoice',
            'res_id': invoice2.id,
            'partner_id': self.partner_without_mail2.id,
        })
        self.env['mail.followers'].create({
            'res_model': 'account.invoice',
            'res_id': invoice2.id,
            'partner_id': self.partner_without_mail.id,
        })
        action_invoice_wizard = invoice.action_invoice_sent()
        ctx = action_invoice_wizard["context"]
        ctx.update({
            "active_id": invoice.id,
            "active_ids": [invoice.id, invoice2.id],
            "active_model": "account.invoice",
        })
        invoice_wizard = (
            self.env[action_invoice_wizard["res_model"]]
            .with_context(ctx)
            .create({})
        )
        invoice_wizard._compute_invoice_without_email()
        self.assertIn(_(
            "The following invoice(s) will not be sent by"
            " email, because some followers don't have email"
            " address."),
            invoice_wizard.invoice_without_email)

    def test_partner_without_mail_follower_with_mail(self):
        invoice = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner_without_mail.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'account_id': self.account.id,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        invoice2 = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner_without_mail2.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'account_id': self.account.id,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        self.env['mail.followers'].sudo().search([
            ('res_model', '=', 'account.invoice'),
            ('res_id', '=', invoice2.id),
            ('partner_id', '=', self.env.user.partner_id.id),
        ]).unlink()
        self.env['mail.followers'].sudo().search([
            ('res_model', '=', 'account.invoice'),
            ('res_id', '=', invoice.id),
            ('partner_id', '=', self.env.user.partner_id.id),
        ]).unlink()
        self.env['mail.followers'].create({
            'res_model': 'account.invoice',
            'res_id': invoice.id,
            'partner_id': self.partner.id,
        })
        self.env['mail.followers'].create({
            'res_model': 'account.invoice',
            'res_id': invoice.id,
            'partner_id': self.partner2.id,
        })
        self.env['mail.followers'].create({
            'res_model': 'account.invoice',
            'res_id': invoice2.id,
            'partner_id': self.partner.id,
        })
        self.env['mail.followers'].create({
            'res_model': 'account.invoice',
            'res_id': invoice2.id,
            'partner_id': self.partner2.id,
        })
        action_invoice_wizard = invoice.action_invoice_sent()
        ctx = action_invoice_wizard["context"]
        ctx.update({
            "active_id": invoice.id,
            "active_ids": [invoice.id, invoice2.id],
            "active_model": "account.invoice",
        })
        invoice_wizard = (
            self.env[action_invoice_wizard["res_model"]]
            .with_context(ctx)
            .create({})
        )
        invoice_wizard._compute_invoice_without_email()
        self.assertFalse(invoice_wizard.invoice_without_email)
