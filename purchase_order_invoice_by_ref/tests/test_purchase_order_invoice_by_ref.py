###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common
from odoo.tools.safe_eval import safe_eval


class TestPurchaseOrderInvoiceByRef(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Product test',
            'standard_price': 10,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
            'supplier': True,
        })

    def create_purchase(self, ref):
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'partner_ref': ref,
        })
        line_obj = self.env['purchase.order.line']
        line = line_obj.new({
            'order_id': purchase.id,
            'product_id': self.product.id,
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
            purchases |= self.create_purchase(ref)
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
        purchase = self.create_purchase('01')
        wizard.find_purchases()
        self.assertNotEquals(purchases, wizard.purchase_ids)
        self.assertEquals(len(wizard.line_ids), 1)
        purchase.button_cancel()
        purchase.unlink()
        wizard.line_ids.unlink()
        wizard.references = '01\n01\n01\n*-02-*\n03...\n04'
        wizard.find_purchases()
        self.assertEquals(len(wizard.references_to_list()), 6)
        self.assertEquals(purchases, wizard.purchase_ids)
        self.assertEquals(len(wizard.line_ids), 3)
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
        self.product.supplier_taxes_id = [(6, 0, tax.ids)]
        refs = ['01', '*-02-*', '03...']
        purchases = self.env['purchase.order'].browse([])
        for ref in refs:
            purchases |= self.create_purchase(ref)
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
