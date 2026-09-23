###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestSaleOrderLineSeason(TransactionCase):
    def setUp(self):
        super().setUp()
        self.season = self.env['product.season'].create({
            'name': 'Season test',
        })
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Product test',
            'standard_price': 10,
            'list_price': 10,
            'season_id': self.season.id,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner 1',
        })

    def create_wizard(self, sales, method='all'):
        ctx = {
            'tracking_disable': True,
            'mail_notrack': True,
            'mail_create_nolog': True,
            'active_model': 'sale.order',
            'active_ids': sales.ids,
            'active_id': sales[0].id}
        payment_obj = self.env['sale.advance.payment.inv'].with_context(ctx)
        payment = payment_obj.create({
            'advance_payment_method': method})
        return payment.with_context(ctx)

    def test_from_sale_to_invoice(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id
        })
        line = self.env['sale.order.line'].new({
            'order_id': sale.id,
            'product_id': self.product.id,
        })
        line.product_id_change()
        line = line.create(line._convert_to_write(line._cache))
        self.assertEquals(line.season_id, self.product.season_id)
        sale_report = self.env['sale.report'].search([
            ('season_id', '=', self.product.season_id.id),
        ])
        self.assertEquals(sale_report.season_id, self.product.season_id)
        sale.action_confirm()
        wizard = self.create_wizard(sale)
        wizard.create_invoices()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids[0]
        self.assertEqual(invoice.state, 'draft')
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        self.assertEquals(invoice.invoice_line_ids[0].season_id, line.season_id)
        invoice_report = self.env['account.invoice.report'].search([
            ('season_id', '=', self.product.season_id.id),
        ])
        self.assertEquals(invoice_report.season_id, self.product.season_id)

    def test_create_invoice(self):
        invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'type': 'in_invoice',
        })
        line = self.env['account.invoice.line'].new({
            'invoice_id': invoice.id,
            'product_id': self.product.id,
            'product_uom_qty': 1.0,
            'product_uom': self.ref('uom.product_uom_unit'),
        })
        line._onchange_product_id()
        line = self.env['account.invoice.line'].with_context({
            'partner_id': self.partner.id
        }).create(line._cache)
        self.assertEquals(line.season_id, self.product.season_id)
        invoice_report = self.env['account.invoice.report'].search([
            ('season_id', '=', self.product.season_id.id),
        ])
        self.assertEquals(invoice_report.season_id, self.product.season_id)
