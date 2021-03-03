###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import time

from odoo.tests.common import TransactionCase


class TestPosOrderToSaleOrder(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test customer',
            'customer': True,
        })
        self.product1 = self.env['product.product'].create({
            'name': 'Test product 1',
            'type': 'product',
            'standard_price': 10,
            'list_price': 100,
            'invoice_policy': 'delivery',
            'taxes_id': [(6, 0, [])],
        })
        self.stock_location = self.env['stock.location'].browse(
            self.ref('stock.stock_location_stock'))
        self.configure_pos()

    def update_qty_on_hand(self, product, location, new_qty):
        wizard = self.env['stock.change.product.qty'].create({
            'product_id': product.id,
            'new_quantity': new_qty,
            'location_id': location.id,
        })
        wizard.change_product_qty()
        self.assertEqual(
            product.with_context(location=location.id).qty_available, new_qty)

    def configure_pos(self):
        self.pos_config = self.env.ref('point_of_sale.pos_config_main')
        self.pos_order_session0 = self.env['pos.session'].create({
            'user_id': 1,
            'config_id': self.pos_config.id
        })
        self.pos_config.open_session_cb()
        self.cash_journal = self.env['account.journal'].create({
            'name': 'CASH journal',
            'type': 'cash',
            'code': 'CSH00',
        })
        self.pos_config.current_session_id.write({
            'journal_ids': [(6, 0, [self.cash_journal.id])],
        })
        account_type_rcv = self.env['account.account.type'].create({
            'name': 'RCV type',
            'type': 'receivable',
        })
        self.account = self.env['account.account'].create({
            'name': 'Receivable',
            'code': 'RCV00',
            'user_type_id': account_type_rcv.id,
            'reconcile': True,
        })
        self.cash_journal.loss_account_id = self.account
        self.pos_statement = self.env['account.bank.statement'].create({
            'balance_start': 0.0,
            'balance_end_real': 0.0,
            'date': time.strftime('%Y-%m-%d'),
            'journal_id': self.cash_journal.id,
            'company_id': self.env.user.company_id.id,
            'name': 'pos session test',
        })
        self.pos_config.current_session_id.write({
            'statement_ids': [(6, 0, [self.pos_statement.id])],
        })

    def create_pos_order(self, partner):
        return self.env['pos.order'].create({
            'company_id': self.env.user.company_id.id,
            'partner_id': partner and partner.id or None,
            'pricelist_id': (
                partner and partner.property_product_pricelist.id
                or self.env.ref('product.list0').id),
            'session_id': self.pos_config.current_session_id.id,
            'lines': [(0, 0, {
                'product_id': self.product1.id,
                'price_unit': self.product1.list_price,
                'discount': 0.0,
                'qty': 1.0,
                'price_subtotal': 100,
                'price_subtotal_incl': 100,
            })],
            'amount_total': 100,
            'amount_tax': 0,
            'amount_paid': 0,
            'amount_return': 0,
        })

    def make_payment_pos(self, pos_order, amount):
        pos_make_payment = self.env['pos.make.payment'].with_context({
            'active_ids': [pos_order.id],
            'active_id': pos_order.id,
        }).create({
            'amount': amount,
            'journal_id': self.cash_journal.id,
        })
        pos_make_payment.with_context({
            'active_id': pos_order.id,
        }).check()
        self.assertEquals(pos_order.state, 'paid')
        self.assertEquals(pos_order.amount_paid, amount)

    def test_pos_order_to_sale_order_one_pos_no_picking_no_invoice(self):
        pos_order1 = self.create_pos_order(self.partner)
        self.assertEquals(len(pos_order1), 1)
        self.assertEquals(len(pos_order1.lines), 1)
        self.assertEquals(pos_order1.state, 'draft')
        self.assertFalse(pos_order1.picking_id)
        wizard = self.env['pos_order_to_sale_order'].with_context({
            'active_model': 'pos.order',
            'active_ids': pos_order1.ids,
            'active_id': pos_order1.id,
        }).create({})
        wizard.action_accept()
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertIn(
            'The pos order has not an associated stock picking.',
            wizard.line_ids.name)
        self.assertEquals(wizard.line_ids.pos_order_id, pos_order1)
        self.assertFalse(pos_order1.sale_id)

    def test_pos_order_to_sale_order_one_pos_with_picking(self):
        pos_order1 = self.create_pos_order(self.partner)
        self.assertEquals(len(pos_order1), 1)
        self.assertEquals(len(pos_order1.lines), 1)
        self.assertEquals(pos_order1.state, 'draft')
        self.assertFalse(pos_order1.picking_id)
        self.assertFalse(pos_order1.invoice_id)
        self.make_payment_pos(pos_order1, 100)
        self.assertEquals(len(pos_order1.picking_id), 1)
        self.assertEqual(pos_order1.picking_id.state, 'done')
        wizard = self.env['pos_order_to_sale_order'].with_context({
            'active_model': 'pos.order',
            'active_ids': pos_order1.ids,
            'active_id': pos_order1.id,
        }).create({})
        wizard.action_accept()
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertTrue(pos_order1.sale_id)
        sale = pos_order1.sale_id
        self.assertEquals(len(sale), 1)
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.order_line), 1)
        self.assertEquals(sale.order_line.product_id, self.product1)
        self.assertEquals(sale.order_line.product_uom_qty, 1)
        self.assertEquals(sale.order_line.price_unit, 100)
        self.assertEquals(sale.order_line.discount, 0)
        self.assertEquals(
            sale.order_line.tax_id, sale.order_line.product_id.taxes_id)
        self.assertEquals(sale.amount_untaxed, 100)
        self.assertEquals(sale.amount_tax, 0)
        self.assertEquals(sale.amount_total, 100)
        self.assertEquals(sale.partner_id, self.partner)
        self.assertEquals(sale.picking_ids.id, pos_order1.picking_id.id)
        self.assertEquals(
            sale.order_line.move_ids, sale.picking_ids.move_lines)
        self.assertEquals(
            sale.order_line.qty_delivered, sale.order_line.product_uom_qty)
        self.assertEquals(sale.order_line.qty_invoiced, 0)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        self.assertEquals(sale.order_line.qty_invoiced, 1)

    def test_pos_order_to_sale_order_several_pos_no_picking_no_invoice(self):
        pos_order1 = self.create_pos_order(self.partner)
        self.assertEquals(len(pos_order1), 1)
        self.assertEquals(len(pos_order1.lines), 1)
        self.assertEquals(pos_order1.state, 'draft')
        self.assertFalse(pos_order1.picking_id)
        pos_order2 = self.create_pos_order(self.partner)
        self.assertEquals(len(pos_order2), 1)
        self.assertEquals(len(pos_order2.lines), 1)
        self.assertEquals(pos_order2.state, 'draft')
        self.assertFalse(pos_order2.picking_id)
        wizard = self.env['pos_order_to_sale_order'].with_context({
            'active_model': 'pos.order',
            'active_ids': [pos_order1.id, pos_order2.id],
            'active_id': pos_order1.id,
        }).create({})
        wizard.action_accept()
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertIn(
            'The pos order has not an associated stock picking.',
            wizard.line_ids[0].name)
        self.assertEquals(wizard.line_ids[0].pos_order_id, pos_order1)
        self.assertIn(
            'The pos order has not an associated stock picking.',
            wizard.line_ids[1].name)
        self.assertEquals(wizard.line_ids[1].pos_order_id, pos_order2)
        self.assertFalse(pos_order2.sale_id)

    def test_pos_order_to_sale_order_several_pos_with_picking(self):
        pos_order1 = self.create_pos_order(self.partner)
        self.assertEquals(len(pos_order1), 1)
        self.assertEquals(len(pos_order1.lines), 1)
        self.assertEquals(pos_order1.state, 'draft')
        self.assertFalse(pos_order1.picking_id)
        self.assertFalse(pos_order1.invoice_id)
        self.make_payment_pos(pos_order1, 100)
        self.assertEquals(len(pos_order1.picking_id), 1)
        pos_order2 = self.create_pos_order(self.partner)
        self.assertEquals(len(pos_order2), 1)
        self.assertEquals(len(pos_order2.lines), 1)
        self.assertEquals(pos_order2.state, 'draft')
        self.assertFalse(pos_order2.picking_id)
        self.assertFalse(pos_order2.invoice_id)
        self.make_payment_pos(pos_order2, 100)
        self.assertEquals(len(pos_order2.picking_id), 1)
        wizard = self.env['pos_order_to_sale_order'].with_context({
            'active_model': 'pos.order',
            'active_ids': [pos_order1.id, pos_order2.id] ,
            'active_id': pos_order1.id,
        }).create({})
        wizard.action_accept()
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertTrue(pos_order1.sale_id)
        sale1 = pos_order1.sale_id
        self.assertEquals(len(sale1), 1)
        self.assertEquals(sale1.state, 'sale')
        self.assertEquals(len(sale1.order_line), 1)
        self.assertEquals(sale1.order_line.product_id, self.product1)
        self.assertEquals(sale1.order_line.product_uom_qty, 1)
        self.assertEquals(sale1.order_line.price_unit, 100)
        self.assertEquals(sale1.order_line.discount, 0)
        self.assertEquals(
            sale1.order_line.tax_id, sale1.order_line.product_id.taxes_id)
        self.assertEquals(sale1.amount_untaxed, 100)
        self.assertEquals(sale1.amount_tax, 0)
        self.assertEquals(sale1.amount_total, 100)
        self.assertEquals(sale1.partner_id, self.partner)
        self.assertEquals(sale1.picking_ids.id, pos_order1.picking_id.id)
        self.assertEquals(
            sale1.order_line.move_ids, sale1.picking_ids.move_lines)
        self.assertEquals(
            sale1.order_line.qty_delivered, sale1.order_line.product_uom_qty)
        self.assertEquals(sale1.order_line.qty_invoiced, 0)
        sale1.action_invoice_create()
        self.assertEquals(len(sale1.invoice_ids), 1)
        self.assertEquals(sale1.order_line.qty_invoiced, 1)
        self.assertTrue(pos_order2.sale_id)
        sale2 = pos_order2.sale_id
        self.assertEquals(len(sale2), 1)
        self.assertEquals(sale2.state, 'sale')
        self.assertEquals(len(sale2.order_line), 1)
        self.assertEquals(sale2.order_line.product_id, self.product1)
        self.assertEquals(sale2.order_line.product_uom_qty, 1)
        self.assertEquals(sale2.order_line.price_unit, 100)
        self.assertEquals(sale2.order_line.discount, 0)
        self.assertEquals(
            sale2.order_line.tax_id, sale2.order_line.product_id.taxes_id)
        self.assertEquals(sale2.amount_untaxed, 100)
        self.assertEquals(sale2.amount_tax, 0)
        self.assertEquals(sale2.amount_total, 100)
        self.assertEquals(sale2.partner_id, self.partner)
        self.assertEquals(sale2.picking_ids.id, pos_order2.picking_id.id)
        self.assertEquals(
            sale2.order_line.move_ids, sale2.picking_ids.move_lines)
        self.assertEquals(
            sale2.order_line.qty_delivered, sale2.order_line.product_uom_qty)
        self.assertEquals(sale2.order_line.qty_invoiced, 0)
        sale2.action_invoice_create()
        self.assertEquals(len(sale2.invoice_ids), 1)
        self.assertEquals(sale2.order_line.qty_invoiced, 1)

    def test_pos_order_to_sale_order_no_partner(self):
        pos_order1 = self.create_pos_order(None)
        self.assertEquals(len(pos_order1), 1)
        self.assertEquals(len(pos_order1.lines), 1)
        self.assertEquals(pos_order1.state, 'draft')
        self.assertFalse(pos_order1.picking_id)
        wizard = self.env['pos_order_to_sale_order'].with_context({
            'active_model': 'pos.order',
            'active_ids': pos_order1.ids,
            'active_id': pos_order1.id,
        }).create({})
        wizard.action_accept()
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertIn(
            'The pos order must have a partner assigned.',
            wizard.line_ids.name)
        self.assertEquals(wizard.line_ids.pos_order_id, pos_order1)
        self.assertFalse(pos_order1.sale_id)

    def test_pos_order_to_sale_order_one_pos_picking_2call_wizard(self):
        pos_order1 = self.create_pos_order(self.partner)
        self.assertEquals(len(pos_order1), 1)
        self.assertEquals(len(pos_order1.lines), 1)
        self.assertEquals(pos_order1.state, 'draft')
        self.assertFalse(pos_order1.picking_id)
        self.make_payment_pos(pos_order1, 100)
        self.assertEquals(len(pos_order1.picking_id), 1)
        self.assertEqual(pos_order1.picking_id.state, 'done')
        wizard = self.env['pos_order_to_sale_order'].with_context({
            'active_model': 'pos.order',
            'active_ids': pos_order1.ids,
            'active_id': pos_order1.id,
        }).create({})
        wizard.action_accept()
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertTrue(pos_order1.sale_id)
        sale1 = pos_order1.sale_id
        self.assertEquals(len(sale1), 1)
        self.assertEquals(sale1.state, 'sale')
        self.assertEquals(len(sale1.order_line), 1)
        self.assertEquals(sale1.order_line.product_id, self.product1)
        self.assertEquals(sale1.order_line.product_uom_qty, 1)
        self.assertEquals(sale1.order_line.price_unit, 100)
        self.assertEquals(sale1.order_line.discount, 0)
        self.assertEquals(
            sale1.order_line.tax_id, sale1.order_line.product_id.taxes_id)
        self.assertEquals(sale1.amount_untaxed, 100)
        self.assertEquals(sale1.amount_tax, 0)
        self.assertEquals(sale1.amount_total, 100)
        self.assertEquals(sale1.partner_id, self.partner)
        self.assertEquals(sale1.picking_ids.id, pos_order1.picking_id.id)
        self.assertEquals(
            sale1.order_line.move_ids, sale1.picking_ids.move_lines)
        self.assertEquals(
            sale1.order_line.qty_delivered, sale1.order_line.product_uom_qty)
        self.assertEquals(sale1.order_line.qty_invoiced, 0)
        sale1.action_invoice_create()
        self.assertEquals(len(sale1.invoice_ids), 1)
        self.assertEquals(sale1.order_line.qty_invoiced, 1)
        wizard = self.env['pos_order_to_sale_order'].with_context({
            'active_model': 'pos.order',
            'active_ids': pos_order1.ids,
            'active_id': pos_order1.id,
        }).create({})
        wizard.action_accept()
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertTrue(pos_order1.sale_id)
        self.assertEquals(pos_order1.sale_id, sale1)
