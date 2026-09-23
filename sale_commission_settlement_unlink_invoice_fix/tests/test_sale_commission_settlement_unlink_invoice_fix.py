###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import dateutil.relativedelta
from odoo import fields
from odoo.tests import common


class TestSaleCommissionSettlementUnlinkInvoiceFix(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'is_company': True,
            'customer': True,
            'supplier': False,
            'agent': False,
        })
        self.product = self.env['product.product'].create({
            'type': 'consu',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 500,
            'list_price': 1000,
            'invoice_policy': 'order',
        })
        self.agent = self.env['res.partner'].create({
            'name': 'Test agent',
            'agent': True,
            'settlement': 'monthly',
        })
        self.commission = self.env['sale.commission'].create({
            'name': 'Fixed commission (Net amount) - Invoice Based',
            'fix_qty': 10.0,
            'amount_base_type': 'net_amount',
        })
        self.journal = self.env['account.journal'].search([
            ('type', '=', 'purchase'),
        ], limit=1)

    def _create_sale_order(self, agent, commission):
        return self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'name': self.product.name,
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'product_uom': self.env.ref('uom.product_uom_unit').id,
                    'price_unit': self.product.lst_price,
                    'agents': [
                        (0, 0, {
                            'agent': agent.id,
                            'commission': commission.id,
                        })
                    ],
                })
            ],
        })

    def test_settlement_invoice_cancel_remove_invoice_01(self):
        sale = self._create_sale_order(self.agent, self.commission)
        self.assertEqual(sale.state, 'draft')
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.invoice_ids), 0)
        sale.action_invoice_create()
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids[0]
        invoice.action_invoice_open()
        self.assertEqual(invoice.state, 'open')
        date_now = fields.Datetime.from_string(fields.Datetime.now())
        period = 1
        date_period = dateutil.relativedelta.relativedelta(months=period)
        wizard = self.env['sale.commission.make.settle'].create({
            'date_to': date_now + date_period
        })
        wizard.action_settle()
        settlements = self.env['sale.commission.settlement'].search([
            ('agent', '=', self.agent.id),
        ])
        self.assertEqual(len(settlements), 1)
        settlement = settlements[0]
        self.assertTrue(settlement.total > 0)
        wizard_02 = self.env['sale.commission.make.invoice'].create({
            'product': 1,
            'journal': self.journal.id,
        })
        self.assertFalse(settlement.invoice)
        wizard_02.button_create()
        self.assertTrue(settlement.invoice)
        self.assertTrue(settlement.invoice.amount_total > 0)
        self.assertEqual(settlement.invoice.type, 'in_invoice')
        self.assertEqual(settlement.invoice.state, 'draft')
        self.assertEqual(settlement.state, 'invoiced')
        settlement.invoice.unlink()
        self.assertFalse(settlement.invoice)
        self.assertEqual(settlement.state, 'settled')

    def test_settlement_invoice_cancel_and_unlink_from_invoice_02(self):
        sale = self._create_sale_order(self.agent, self.commission)
        self.assertEqual(sale.state, 'draft')
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.invoice_ids), 0)
        sale.action_invoice_create()
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids[0]
        invoice.action_invoice_open()
        self.assertEqual(invoice.state, 'open')
        date_now = fields.Datetime.from_string(fields.Datetime.now())
        period = 1
        date_period = dateutil.relativedelta.relativedelta(months=period)
        wizard = self.env['sale.commission.make.settle'].create({
            'date_to': date_now + date_period
        })
        wizard.action_settle()
        settlements = self.env['sale.commission.settlement'].search([
            ('agent', '=', self.agent.id),
        ])
        self.assertEqual(len(settlements), 1)
        settlement = settlements[0]
        self.assertTrue(settlement.total > 0)
        wizard_02 = self.env['sale.commission.make.invoice'].create({
            'product': 1,
            'journal': self.journal.id,
        })
        self.assertFalse(settlement.invoice)
        wizard_02.button_create()
        self.assertTrue(settlement.invoice)
        self.assertTrue(settlement.invoice.amount_total > 0)
        self.assertEqual(settlement.invoice.type, 'in_invoice')
        self.assertEqual(settlement.invoice.state, 'draft')
        self.assertEqual(settlement.state, 'invoiced')
        settlement.invoice.action_cancel()
        self.assertTrue(settlement.invoice)
        self.assertEqual(settlement.state, 'except_invoice')
        settlement.invoice.unlink()
        self.assertFalse(settlement.invoice)
        self.assertEqual(settlement.state, 'settled')

    def test_settlement_invoice_cancel_draft_03(self):
        sale = self._create_sale_order(self.agent, self.commission)
        self.assertEqual(sale.state, 'draft')
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.invoice_ids), 0)
        sale.action_invoice_create()
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids[0]
        invoice.action_invoice_open()
        self.assertEqual(invoice.state, 'open')
        date_now = fields.Datetime.from_string(fields.Datetime.now())
        period = 1
        date_period = dateutil.relativedelta.relativedelta(months=period)
        wizard = self.env['sale.commission.make.settle'].create({
            'date_to': date_now + date_period
        })
        wizard.action_settle()
        settlements = self.env['sale.commission.settlement'].search([
            ('agent', '=', self.agent.id),
        ])
        self.assertEqual(len(settlements), 1)
        settlement = settlements[0]
        self.assertTrue(settlement.total > 0)
        wizard_02 = self.env['sale.commission.make.invoice'].create({
            'product': 1,
            'journal': self.journal.id,
        })
        self.assertFalse(settlement.invoice)
        wizard_02.button_create()
        self.assertTrue(settlement.invoice)
        self.assertTrue(settlement.invoice.amount_total > 0)
        self.assertEqual(settlement.invoice.type, 'in_invoice')
        self.assertEqual(settlement.invoice.state, 'draft')
        self.assertEqual(settlement.state, 'invoiced')
        settlement.invoice.action_cancel()
        self.assertTrue(settlement.invoice)
        self.assertEqual(settlement.invoice.state, 'cancel')
        self.assertEqual(settlement.state, 'except_invoice')
        settlement.invoice.action_invoice_draft()
        self.assertEqual(settlement.state, 'invoiced')
