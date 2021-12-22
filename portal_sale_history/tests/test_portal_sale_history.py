###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class SalePortal(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 10})]
        })
        self.acquirer = self.env.ref('payment.payment_acquirer_paypal')
        self.currency_euro = self.env.ref("base.EUR")
        self.country_spain = self.env.ref("base.es")

    def test_received_order_only(self):
        self.assertIn('Received order', self.sale.get_order_status_info()[0])
        self.assertIn(
            self.sale.date_order, self.sale.get_order_status_info()[0])

    def test_received_confirmed_shipped_order(self):
        self.sale.action_confirm()
        self.assertIn('Received order', self.sale.get_order_status_info()[0])
        self.assertIn(
            self.sale.date_order, self.sale.get_order_status_info()[0])
        tx = self.env['payment.transaction'].create({
            'amount': self.sale.amount_total,
            'sale_oder_ids': self.sale.id,
            'acquirer_id': self.acquirer.id,
            'currency_id': self.currency_euro.id,
            'reference': 'test_ref_2',
            'partner_name': 'Norbert Buyer',
            'partner_country_id': self.country_spain.id})
        self.sale.transaction_ids = tx.ids
        self.assertIn(
            'Waiting for payment confirmation from: Paypal',
            self.sale.get_order_status_info()[1])
        tx._set_transaction_done()
        self.assertIn(
            'Payment accepted with: Paypal',
            self.sale.get_order_status_info()[1])
        self.assertIn('Confirmed order', self.sale.get_order_status_info()[2])
        self.assertIn(
            self.sale.confirmation_date, self.sale.get_order_status_info()[2])
        self.sale.action_invoice_create()
        picking = self.sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertIn('Shipped order', self.sale.get_order_status_info()[3])

    def test_received_cancell_order(self):
        self.sale.action_cancel()
        self.assertIn('Received order', self.sale.get_order_status_info()[0])
        self.assertIn(
            self.sale.date_order, self.sale.get_order_status_info()[0])

        self.assertIn('Cancelled order', self.sale.get_order_status_info()[1])
        self.assertIn(
            self.sale.cancelled_date, self.sale.get_order_status_info()[1])

    def test_received_fail_payment_order(self):
        self.assertIn('Received order', self.sale.get_order_status_info()[0])
        self.assertIn(
            self.sale.date_order, self.sale.get_order_status_info()[0])
        tx = self.env['payment.transaction'].create({
            'amount': self.sale.amount_total,
            'sale_oder_ids': self.sale.id,
            'acquirer_id': self.acquirer.id,
            'currency_id': self.currency_euro.id,
            'reference': 'test_ref_2',
            'partner_name': 'Norbert Buyer',
            'partner_country_id': self.country_spain.id})
        self.sale.transaction_ids = tx.ids
        self.assertIn(
            'Waiting for payment confirmation from: Paypal',
            self.sale.get_order_status_info()[1])
        tx._set_transaction_cancel()
        self.assertIn(
            'Payment cancelled', self.sale.get_order_status_info()[1])
