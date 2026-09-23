###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common
from odoo.tools.safe_eval import safe_eval


class TestPurchaseOrderInvoiceByRef(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.product_service = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Product service test',
            'standard_price': 10,
            'purchase_method': 'receive',
        })
        self.product_stock_01 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test purchase method',
            'standard_price': 10,
            'purchase_method': 'purchase',
        })
        self.product_stock_02 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test purchase method',
            'standard_price': 10,
            'purchase_method': 'receive',
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
            'supplier': True,
        })

    def create_purchase(self, ref, product):
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'partner_ref': ref,
        })
        line_obj = self.env['purchase.order.line']
        line = line_obj.new({
            'order_id': purchase.id,
            'product_id': product.id,
            'product_uom_qty': 1
        })
        line.onchange_product_id()
        line['price_unit'] = 100
        line_obj.create(line_obj._convert_to_write(line._cache))
        purchase.button_confirm()
        return purchase

    def test_purchase_order(self):
        refs = ['01', '*-02-*', '03...']
        purchases = self.env['purchase.order'].browse([])
        for ref in refs:
            purchases |= self.create_purchase(ref, self.product_service)
        self.assertEquals(len(purchases), 3)
        wizard = self.env['purchase.order.invoice_refs'].create({
            'partner_id': self.partner.id,
            'references': '\n'.join(refs),
            'method': 'all',
            'join_purchases': True,
        })
        self.assertEquals(wizard.partner_id, self.partner)
        self.assertFalse(
            [e for e in wizard.references_to_list() if e not in refs])
        wizard.find_purchases()
        self.assertEquals(wizard.partner_id, self.partner)
        self.assertEquals(purchases, wizard.purchase_ids)
        wizard.references = '01 \n *-02-* \n 03...\n   \n \n'
        wizard.find_purchases()
        self.assertEquals(purchases, wizard.purchase_ids)
        self.assertEquals(len(wizard.line_ids), 0)
        purchase = self.create_purchase('01', self.product_service)
        wizard.find_purchases()
        self.assertNotEquals(purchases, wizard.purchase_ids)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertIn('01', wizard.line_ids.ref)
        self.assertIn('Return more than one purchase.', wizard.line_ids.name)
        self.assertEquals(wizard.line_ids.type, 'error')
        purchase.button_cancel()
        purchase.unlink()
        wizard.line_ids.unlink()
        wizard.references = '01\n01\n01\n*-02-*\n03...\n04'
        wizard.find_purchases()
        self.assertEquals(len(wizard.references_to_list()), 6)
        self.assertEquals(purchases, wizard.purchase_ids)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertIn('01', wizard.line_ids[0].ref)
        self.assertIn(
            'Reference duplicate, ignore one.', wizard.line_ids[0].name)
        self.assertEquals(wizard.line_ids[0].type, 'warning')
        self.assertIn('01', wizard.line_ids[1].ref)
        self.assertIn(
            'Reference duplicate, ignore one.', wizard.line_ids[1].name)
        self.assertEquals(wizard.line_ids[1].type, 'warning')
        self.assertIn('04', wizard.line_ids[2].ref)
        self.assertIn('Purchase not found.', wizard.line_ids[2].name)
        self.assertEquals(wizard.line_ids[2].type, 'error')
        wizard.references = '01\n*-02-*\n03...\n'
        wizard.action_find()
        self.assertEquals(purchases, wizard.purchase_ids)
        wizard.action_invoice()
        self.assertEquals(len(purchases[0].invoice_ids), 1)

    def test_purchase_order_with_taxs(self):
        tax_group_taxes = self.env.ref('account.tax_group_taxes')
        tax = self.env['account.tax'].create({
            'name': 'Tax for purchase 10%',
            'type_tax_use': 'purchase',
            'tax_group_id': tax_group_taxes.id,
            'amount_type': 'percent',
            'amount': 10.0,
        })
        self.product_service.supplier_taxes_id = [(6, 0, tax.ids)]
        refs = ['01', '*-02-*', '03...']
        purchases = self.env['purchase.order'].browse([])
        for ref in refs:
            purchases |= self.create_purchase(ref, self.product_service)
        self.assertEquals(purchases[0].order_line.taxes_id[0], tax)
        wizard = self.env['purchase.order.invoice_refs'].create({
            'partner_id': self.partner.id,
            'references': '\n'.join(refs),
            'method': 'all',
            'join_purchases': True,
        })
        wizard.action_find()
        self.assertEquals(purchases, wizard.purchase_ids)
        action = wizard.action_invoice()
        invoice = self.env['account.invoice'].search(
            safe_eval(action['domain']))
        self.assertEquals(len(invoice), 1)
        self.assertEquals(invoice.amount_tax, 30)

    def test_purchase_order_with_refund_invoice_purchase_method(self):
        ref = '01'
        purchase = self.env['purchase.order'].browse([])
        purchase |= self.create_purchase(ref, self.product_stock_01)
        self.assertEquals(len(purchase), 1)
        self.assertEquals(len(purchase.picking_ids), 1)
        picking = purchase.picking_ids
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        wizard = self.env['purchase.order.invoice_refs'].create({
            'partner_id': self.partner.id,
            'references': ref,
            'method': 'all',
            'join_purchases': True,
        })
        self.assertEquals(wizard.partner_id, self.partner)
        wizard.find_purchases()
        self.assertEquals(wizard.partner_id, self.partner)
        self.assertEquals(purchase, wizard.purchase_ids)
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_invoice()
        self.assertEquals(len(purchase.invoice_ids), 1)
        invoice = purchase.invoice_ids
        invoice.action_invoice_open()
        self.assertEquals(invoice.type, 'in_invoice')
        self.env['account.invoice.refund'].with_context(
            active_ids=invoice.ids).create({
                'filter_refund': 'refund',
                'description': 'Refund reason',
            }).invoice_refund()
        self.assertEquals(len(purchase.invoice_ids), 2)
        invoice_refund = purchase.invoice_ids - invoice
        self.assertEquals(len(invoice_refund), 1)
        self.assertEquals(invoice_refund.type, 'in_refund')
        wizard = self.env['purchase.order.invoice_refs'].create({
            'partner_id': self.partner.id,
            'references': ref,
            'method': 'all',
            'join_purchases': True,
        })
        self.assertEquals(wizard.partner_id, self.partner)
        wizard.find_purchases()
        self.assertEquals(wizard.partner_id, self.partner)
        self.assertEquals(purchase, wizard.purchase_ids)
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_invoice()
        self.assertEquals(len(purchase.invoice_ids), 3)
        new_invoice = purchase.invoice_ids - invoice - invoice_refund
        self.assertEquals(len(new_invoice), 1)
        self.assertEquals(new_invoice.type, 'in_invoice')

    def test_purchase_order_with_refund_invoice_purchase_method_receive(self):
        ref = '01'
        purchase = self.env['purchase.order'].browse([])
        purchase |= self.create_purchase(ref, self.product_stock_02)
        self.assertEquals(len(purchase), 1)
        self.assertEquals(len(purchase.picking_ids), 1)
        picking = purchase.picking_ids
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        wizard = self.env['purchase.order.invoice_refs'].create({
            'partner_id': self.partner.id,
            'references': ref,
            'method': 'all',
            'join_purchases': True,
        })
        self.assertEquals(wizard.partner_id, self.partner)
        wizard.find_purchases()
        self.assertEquals(wizard.partner_id, self.partner)
        self.assertEquals(purchase, wizard.purchase_ids)
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_invoice()
        self.assertEquals(len(purchase.invoice_ids), 1)
        invoice = purchase.invoice_ids
        invoice.action_invoice_open()
        self.assertEquals(invoice.type, 'in_invoice')
        self.env['account.invoice.refund'].with_context(
            active_ids=invoice.ids).create({
                'filter_refund': 'refund',
                'description': 'Refund reason',
            }).invoice_refund()
        self.assertEquals(len(purchase.invoice_ids), 2)
        invoice_refund = purchase.invoice_ids - invoice
        self.assertEquals(len(invoice_refund), 1)
        self.assertEquals(invoice_refund.type, 'in_refund')
        wizard = self.env['purchase.order.invoice_refs'].create({
            'partner_id': self.partner.id,
            'references': ref,
            'method': 'all',
            'join_purchases': True,
        })
        self.assertEquals(wizard.partner_id, self.partner)
        wizard.find_purchases()
        self.assertEquals(wizard.partner_id, self.partner)
        self.assertEquals(purchase, wizard.purchase_ids)
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_invoice()
        self.assertEquals(len(purchase.invoice_ids), 3)
        new_invoice = purchase.invoice_ids - invoice - invoice_refund
        self.assertEquals(len(new_invoice), 1)
        self.assertEquals(new_invoice.type, 'in_invoice')
