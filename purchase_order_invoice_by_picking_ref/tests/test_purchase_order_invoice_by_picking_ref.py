###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestPurchaseOrderInvoiceByPickingRef(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'type': 'product',
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
        self.assertEquals(len(wizard.line_ids), 4)
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
        self.assertIn('04', wizard.line_ids[3].ref)
        self.assertIn('Picking not found.', wizard.line_ids[3].name)
        self.assertEquals(wizard.line_ids[3].type, 'error')
        wizard.references = '01\n*-02-*\n03...\n'
        wizard.action_find()
        self.assertEquals(purchases, wizard.purchase_ids)
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_invoice()
        self.assertEquals(len(purchases[0].invoice_ids), 1)

    def test_picking_only(self):
        picking_refs = ['XXA', '*-XXB-*', 'XXC...']
        purchases = self.env['purchase.order'].browse([])
        for picking_ref in picking_refs:
            new_purchase = self.create_purchase('')
            picking = new_purchase.picking_ids
            picking.picking_supplier_ref = picking_ref
            picking.action_confirm()
            picking.action_assign()
            for move in picking.move_lines:
                move.quantity_done = move.product_uom_qty
            picking.action_done()
            purchases |= new_purchase
        self.assertEquals(len(purchases), 3)
        wizard = self.env['purchase.order.invoice_refs'].create({
            'partner_id': self.partner.id,
            'references': '\n'.join(picking_refs),
            'method': 'all',
            'join_purchases': True,
        })
        self.assertEquals(wizard.partner_id, self.partner)
        self.assertFalse(
            [e for e in wizard.references_to_list() if e not in picking_refs])
        wizard.find_purchases()
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.partner_id, self.partner)
        self.assertEquals(purchases, wizard.purchase_ids)
        wizard.references = 'XXA \n *-XXB-* \n XXC...\n   \n \n'
        wizard.find_purchases()
        self.assertEquals(purchases, wizard.purchase_ids)
        self.assertEquals(len(wizard.line_ids), 0)
        purchase = self.create_purchase('01')
        picking = purchase.picking_ids
        picking.picking_supplier_ref = 'XXC...'
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        wizard.find_purchases()
        self.assertNotEquals(purchases, wizard.purchase_ids)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertIn('XXC...', wizard.line_ids[0].ref)
        self.assertIn('Purchase not found.', wizard.line_ids[0].name)
        self.assertEquals(wizard.line_ids[0].type, 'error')
        self.assertIn('XXC...', wizard.line_ids[1].ref)
        self.assertIn('Return more than one picking.', wizard.line_ids[1].name)
        self.assertEquals(wizard.line_ids[1].type, 'error')
        wizard.action_invoice()
        self.assertEquals(len(purchases.mapped('invoice_ids')), 1)

    def test_purchase_order_and_pickings(self):
        refs = ['01', '*-02-*', '03...']
        purchases = self.env['purchase.order'].browse([])
        for ref in refs:
            purchases |= self.create_purchase(ref)
        picking_refs = ['XXA', '*-XXB-*', 'XXC...']
        for picking_ref in picking_refs:
            new_purchase = self.create_purchase('')
            picking = new_purchase.picking_ids
            picking.picking_supplier_ref = picking_ref
            picking.action_confirm()
            picking.action_assign()
            for move in picking.move_lines:
                move.quantity_done = move.product_uom_qty
            picking.action_done()
            purchases |= new_purchase
        self.assertEquals(len(purchases), 6)
        wizard = self.env['purchase.order.invoice_refs'].create({
            'partner_id': self.partner.id,
            'references': '\n'.join(refs + picking_refs),
            'method': 'all',
            'join_purchases': True,
        })
        self.assertEquals(wizard.partner_id, self.partner)
        self.assertFalse([
            e for e in wizard.references_to_list()
            if e not in refs + picking_refs])
        wizard.find_purchases()
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.partner_id, self.partner)
        self.assertEquals(purchases, wizard.purchase_ids)
        wizard.references = '01 \n *-02-* \n 03...\n   \n \n'
        wizard.find_purchases()
        self.assertNotEquals(purchases, wizard.purchase_ids)
        self.assertEquals(len(wizard.line_ids), 0)
        purchase = self.create_purchase('01')
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
        self.assertNotEquals(purchases, wizard.purchase_ids)
        self.assertEquals(len(wizard.line_ids), 4)
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
        self.assertIn('04', wizard.line_ids[3].ref)
        self.assertIn('Picking not found.', wizard.line_ids[3].name)
        self.assertEquals(wizard.line_ids[3].type, 'error')
        wizard.references = '01\n*-02-*\n03...\n'
        wizard.action_find()
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertNotEquals(purchases, wizard.purchase_ids)
        purchase = self.create_purchase('01')
        picking = purchase.picking_ids
        picking.picking_supplier_ref = 'XXC...'
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        wizard.references = 'XXA \n *-XXB-* \n XXC...\n   \n \n'
        wizard.find_purchases()
        self.assertNotEquals(purchases, wizard.purchase_ids)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertIn('XXC...', wizard.line_ids[0].ref)
        self.assertIn('Purchase not found.', wizard.line_ids[0].name)
        self.assertEquals(wizard.line_ids[0].type, 'error')
        self.assertIn('XXC...', wizard.line_ids[1].ref)
        self.assertIn('Return more than one picking.', wizard.line_ids[1].name)
        self.assertEquals(wizard.line_ids[1].type, 'error')
        wizard.action_invoice()
        self.assertEquals(len(purchases.mapped('invoice_ids')), 1)
