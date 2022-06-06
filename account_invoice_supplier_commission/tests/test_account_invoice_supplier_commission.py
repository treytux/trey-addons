###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestAccountInvoiceSupplierCommission(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.commission = self.env['sale.commission'].create({
            'name': '10% fixed commission - Invoice Based',
            'fix_qty': 10.0,
            'commission_type': 'fixed',
        })
        self.partner_agent = self.env['res.partner'].create({
            'name': 'Partner test',
            'agent': True,
            'commission': self.commission.id,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'agents': [(4, self.partner_agent.id)],
        })
        self.product = self.env['product.product'].create({
            'name': 'Product test',
            'invoice_policy': 'order',
            'type': 'consu',
            'company_id': False,
            'standard_price': 100,
            'list_price': 100,
        })
        self.product_free_commission = self.env['product.product'].create({
            'name': 'Product test',
            'invoice_policy': 'order',
            'type': 'consu',
            'commission_free': True,
            'company_id': False,
            'standard_price': 100,
            'list_price': 100,
        })

    def test_create_in_invoice_with_commission(self):
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
        self.assertEqual(line.agents.commission, self.commission)
        self.assertEqual(invoice.amount_total, 100)
        self.assertEqual(invoice.commission_total, -10.0)
        line.product_id = self.product_free_commission.id
        line._onchange_product_id()
        self.assertEqual(line.agents.commission, self.commission)
        self.assertEqual(invoice.amount_total, 100)
        self.assertEqual(invoice.commission_total, 0.0)

    def test_create_in_refund_no_commission(self):
        invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'type': 'in_refund',
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
        self.assertEqual(line.agents.commission, self.commission)
        self.assertEqual(invoice.amount_total, 100)
        self.assertEqual(invoice.commission_total, 10.0)
        line.product_id = self.product_free_commission.id
        line._onchange_product_id()
        self.assertEqual(line.agents.commission, self.commission)
        self.assertEqual(invoice.amount_total, 100)
        self.assertEqual(invoice.commission_total, 0.0)

    def test_create_out_invoice_with_commission(self):
        invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'type': 'out_invoice',
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
        self.assertEqual(line.agents.commission, self.commission)
        self.assertEqual(invoice.amount_total, 100)
        self.assertEqual(invoice.commission_total, 10.0)
        line.product_id = self.product_free_commission.id
        line._onchange_product_id()
        self.assertEqual(line.agents.commission, self.commission)
        self.assertEqual(invoice.amount_total, 100)
        self.assertEqual(invoice.commission_total, 0.0)

    def test_create_out_refund_no_commission(self):
        invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'type': 'out_refund',
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
        self.assertEqual(line.agents.commission, self.commission)
        self.assertEqual(invoice.amount_total, 100)
        self.assertEqual(invoice.commission_total, -10.0)
        line.product_id = self.product_free_commission.id
        line._onchange_product_id()
        self.assertEqual(line.agents.commission, self.commission)
        self.assertEqual(invoice.amount_total, 100)
        self.assertEqual(invoice.commission_total, 0.0)
