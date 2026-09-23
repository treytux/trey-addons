###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import dateutil.relativedelta
from odoo import fields
from odoo.tests import common


class TestSaleCommissionSettlementInvoiceNegative(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env.ref('base.res_partner_2')
        self.partner.write({
            'supplier': False,
            'agent': False,
        })
        self.product = self.env.ref('product.product_product_5')
        self.product.write({
            'invoice_policy': 'order',
            'list_price': 1000,
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
        self.invoice_sequence = self.env['ir.sequence'].create({
            'name': 'Test invoice sequence',
            'padding': 3,
            'prefix': 'tINV',
            'number_next': 5,
        })
        self.refund_sequence = self.env['ir.sequence'].create({
            'name': 'Test refund sequence',
            'padding': 3,
            'prefix': 'tREF',
            'number_next': 10,
        })

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

    def test_sale_commission_settlement_negative_invoice_01(self):
        module = self.env['ir.module.module'].search([
            ('name', '=', 'l10n_es_account_invoice_sequence'),
        ])
        if module.state == 'installed':
            self.assertTrue(self.journal.invoice_sequence_id)
            self.assertFalse(self.journal.refund_inv_sequence_id)
            self.journal.invoice_sequence_id = self.invoice_sequence.id
            self.assertEqual(
                self.journal.invoice_sequence_id, self.invoice_sequence)
        period = 1
        sale = self._create_sale_order(self.agent, self.commission)
        self.assertEqual(sale.state, 'draft')
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.invoice_ids), 0)
        payment = self.env['sale.advance.payment.inv'].create({
            'advance_payment_method': 'all',
        })
        context = {
            'active_model': 'sale.order',
            'active_ids': [sale.id],
            'active_id': sale.id,
        }
        payment.with_context(context).create_invoices()
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids[0]
        invoice.action_invoice_open()
        self.assertEqual(invoice.state, 'open')
        date_now = fields.Datetime.from_string(fields.Datetime.now())
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
        settlement.invoice.action_invoice_open()
        self.assertEqual(settlement.invoice.state, 'open')
        self.assertIn('tINV', settlement.invoice.number)
        refund = invoice.refund()
        refund.action_invoice_open()
        wizard = self.env['sale.commission.make.settle'].create({
            'date_to': date_now + date_period
        })
        wizard.action_settle()
        settlements = self.env['sale.commission.settlement'].search([
            ('agent', '=', self.agent.id),
        ])
        self.assertEqual(len(settlements), 2)
        self.assertTrue(settlements.filtered(lambda r: r.total < 0))
        settlement_negative = settlements.filtered(lambda r: r.total < 0)
        self.assertEqual(len(settlement_negative), 1)
        wizard_03 = self.env['sale.commission.make.invoice'].create({
            'product': 1,
            'journal': self.journal.id,
        })
        self.assertFalse(settlement_negative.invoice)
        wizard_03.button_create()
        self.assertTrue(settlement_negative.invoice)
        self.assertTrue(settlement_negative.invoice.amount_total > 0)
        self.assertEqual(
            settlement.invoice.amount_total,
            settlement_negative.invoice.amount_total)
        self.assertEqual(settlement_negative.invoice.type, 'in_refund')
        self.assertEqual(settlement_negative.invoice.state, 'draft')
        settlement_negative.invoice.action_invoice_open()
        self.assertEqual(settlement_negative.invoice.state, 'open')
        self.assertNotIn('tREF', settlement_negative.invoice.number)
        self.assertIn('tINV', settlement_negative.invoice.number)

    def test_sale_commission_settlement_negative_invoice_02(self):
        module = self.env['ir.module.module'].search([
            ('name', '=', 'l10n_es_account_invoice_sequence'),
        ])
        if module.state == 'installed':
            self.assertTrue(self.journal.invoice_sequence_id)
            self.assertFalse(self.journal.refund_inv_sequence_id)
            self.journal.write({
                'invoice_sequence_id': self.invoice_sequence.id,
                'refund_inv_sequence_id': self.refund_sequence.id,
            })
            self.assertEqual(
                self.journal.invoice_sequence_id, self.invoice_sequence)
            self.assertEqual(
                self.journal.refund_inv_sequence_id, self.refund_sequence)
        else:
            self.skipTest(
                'Module l10n_es_account_invoice_sequence not installed')
        period = 1
        sale = self._create_sale_order(self.agent, self.commission)
        self.assertEqual(sale.state, 'draft')
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.invoice_ids), 0)
        payment = self.env['sale.advance.payment.inv'].create({
            'advance_payment_method': 'all',
        })
        context = {
            'active_model': 'sale.order',
            'active_ids': [sale.id],
            'active_id': sale.id,
        }
        payment.with_context(context).create_invoices()
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids[0]
        invoice.action_invoice_open()
        self.assertEqual(invoice.state, 'open')
        date_now = fields.Datetime.from_string(fields.Datetime.now())
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
        settlement.invoice.action_invoice_open()
        self.assertEqual(settlement.invoice.state, 'open')
        self.assertIn('tINV', settlement.invoice.number)
        self.assertEqual('tINV005', settlement.invoice.number)
        refund = invoice.refund()
        refund.action_invoice_open()
        wizard = self.env['sale.commission.make.settle'].create({
            'date_to': date_now + date_period
        })
        wizard.action_settle()
        settlements = self.env['sale.commission.settlement'].search([
            ('agent', '=', self.agent.id),
        ])
        self.assertEqual(len(settlements), 2)
        self.assertTrue(settlements.filtered(lambda r: r.total < 0))
        settlement_negative = settlements.filtered(lambda r: r.total < 0)
        self.assertEqual(len(settlement_negative), 1)
        wizard_03 = self.env['sale.commission.make.invoice'].create({
            'product': 1,
            'journal': self.journal.id,
        })
        self.assertFalse(settlement_negative.invoice)
        wizard_03.button_create()
        self.assertTrue(settlement_negative.invoice)
        self.assertTrue(settlement_negative.invoice.amount_total > 0)
        self.assertEqual(
            settlement.invoice.amount_total,
            settlement_negative.invoice.amount_total)
        self.assertEqual(settlement_negative.invoice.type, 'in_refund')
        self.assertEqual(settlement_negative.invoice.state, 'draft')
        settlement_negative.invoice.action_invoice_open()
        self.assertEqual(settlement_negative.invoice.state, 'open')
        self.assertIn('tREF', settlement_negative.invoice.number)
