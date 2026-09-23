# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import exceptions, fields
import openerp.tests.common as common


class TestPurchaseStockReport(common.TransactionCase):

    def setUp(self):
        super(TestPurchaseStockReport, self).setUp()
        self.journal_purchase = self.env['account.journal'].create({
            'name': 'Purchase journal',
            'code': 'PUR',
            'type': 'purchase',
        })
        self.journal_purchase_refund = self.env['account.journal'].create({
            'name': 'Purchase refund journal',
            'code': 'RPUR',
            'type': 'purchase_refund',
        })
        self.account_suppliers = self.env['account.account'].create({
            'name': 'Suppliers',
            'code': '410000',
            'type': 'other',
            'user_type': self.env.ref('account.data_account_type_payable').id,
            'reconcile': True,
        })
        self.customer = self.env['res.partner'].create({
            'name': 'Customer',
            'is_company': True,
            'customer': True,
        })
        self.supplier = self.env['res.partner'].create({
            'name': 'Supplier',
            'is_company': True,
            'supplier': True,
            'property_account_payable': self.account_suppliers.id,
        })
        user_types = self.env['account.account.type'].search([])
        if not user_types:
            raise exceptions.Warning('Does not exist any account account type')
        self.user_type = user_types[0]
        self.account = self.env['account.account'].create({
            'name': 'Account for test module',
            'type': 'other',
            'user_type': self.user_type.id,
            'code': '11111',
            'currency_mode': 'current',
            'company_id': self.ref('base.main_company'),
        })
        self.product_01 = self.env['product.product'].create({
            'name': 'Product 01',
            'type': 'product',
            'property_account_expense': self.account.id,
        })
        self.stock_location = self.env.ref('stock.stock_location_stock')
        self.purchase_01 = self.env['purchase.order'].create({
            'partner_id': self.supplier.id,
            'location_id': self.stock_location.id,
            'pricelist_id': self.ref('purchase.list0'),
            'invoice_method': 'picking',
        })
        line_obj = self.env['purchase.order.line']
        line = line_obj.new({
            'order_id': self.purchase_01.id,
            'product_id': self.product_01.id,
            'name': self.product_01.name,
            'price_unit': 100,
            'product_qty': 10,
            'date_planned': fields.Date.today(),
        })
        line.onchange_product_id(
            self.purchase_01.partner_id.property_product_pricelist_purchase.id,
            line.product_id.id, line.product_qty, line.product_uom.id,
            self.purchase_01.partner_id.id)
        line_obj.create(line_obj._convert_to_write(line._cache))
        self.purchase_01.signal_workflow('purchase_confirm')
        picking = self.purchase_01.picking_ids
        self.assertEqual(len(picking), 1)
        self.assertEqual(picking.state, 'assigned')
        self.purchase_02 = self.env['purchase.order'].create({
            'partner_id': self.supplier.id,
            'location_id': self.stock_location.id,
            'pricelist_id': self.ref('purchase.list0'),
            'invoice_method': 'order',
        })
        line_obj = self.env['purchase.order.line']
        line = line_obj.new({
            'order_id': self.purchase_02.id,
            'product_id': self.product_01.id,
            'name': self.product_01.name,
            'price_unit': 100,
            'product_qty': 2,
            'date_planned': fields.Date.today(),
        })
        line.onchange_product_id(
            self.purchase_02.partner_id.property_product_pricelist_purchase.id,
            line.product_id.id, line.product_qty, line.product_uom.id,
            self.purchase_02.partner_id.id)
        line_obj.create(line_obj._convert_to_write(line._cache))
        line = line_obj.new({
            'order_id': self.purchase_02.id,
            'product_id': self.product_01.id,
            'name': self.product_01.name,
            'price_unit': 100,
            'product_qty': 8,
            'date_planned': fields.Date.today(),
        })
        line.onchange_product_id(
            self.purchase_02.partner_id.property_product_pricelist_purchase.id,
            line.product_id.id, line.product_qty, line.product_uom.id,
            self.purchase_02.partner_id.id)
        line_obj.create(line_obj._convert_to_write(line._cache))
        self.purchase_02.signal_workflow('purchase_confirm')
        picking = self.purchase_02.picking_ids
        self.assertEqual(len(picking), 1)
        self.assertEqual(picking.state, 'assigned')

    def is_installed(self, module):
        module = self.env['ir.module.module'].search([
            ('name', '=', 'sale'),
        ], limit=1)
        if module.state != 'installed':
            self.skipTest('sale module not installed, ignore sale tests.')

    def get_real_stock(self, product, location):
        qty_product_dict = product.with_context(
            location=location.id)._product_available()
        return qty_product_dict[product.id]['qty_available']

    def update_stock(self, product, location, qty, lot=None):
        wiz = self.env['stock.change.product.qty'].create({
            'product_id': product.id,
            'new_quantity': qty,
            'location_id': location.id,
            'lot_id': lot and lot.id or None,
        })
        wiz.change_product_qty()
        qty_stock = self.get_real_stock(product, location)
        self.assertEqual(qty_stock, qty)

    def test_po_1_line_transfer_same_qty(self):
        picking = self.purchase_01.picking_ids
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_uom_qty, 10)
        transfer_details = picking.do_enter_transfer_details()
        wizard_model = transfer_details.get('res_model')
        wizard_id = transfer_details.get('res_id')
        wizard_transfer = self.env[wizard_model].browse(wizard_id)
        self.assertEqual(len(wizard_transfer.item_ids), 1)
        self.assertEqual(wizard_transfer.item_ids.quantity, 10)
        wizard_transfer.do_detailed_transfer()
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_uom_qty, 10.0)
        self.assertEqual(
            picking.move_lines.purchase_line_id, self.purchase_01.order_line)

    def test_po_1_line_extra_move_with_linked_move_operation_ids(self):
        picking = self.purchase_01.picking_ids
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_uom_qty, 10)
        transfer_details = picking.do_enter_transfer_details()
        wizard_model = transfer_details.get('res_model')
        wizard_id = transfer_details.get('res_id')
        wizard_transfer = self.env[wizard_model].browse(wizard_id)
        self.assertEqual(len(wizard_transfer.item_ids), 1)
        self.assertEqual(wizard_transfer.item_ids.quantity, 10)
        wizard_transfer.item_ids[0].split_quantities()
        self.assertEqual(len(wizard_transfer.item_ids), 2)
        self.assertEqual(
            wizard_transfer.item_ids.mapped('quantity'), [9.0, 1.0])
        item_qty_1 = wizard_transfer.item_ids.filtered(
            lambda ln: ln.quantity == 1.0)
        self.assertEqual(len(item_qty_1), 1)
        item_qty_1.quantity = 10
        wizard_transfer.do_detailed_transfer()
        self.assertEqual(len(picking.move_lines), 2)
        self.assertIn(9.0, picking.move_lines.mapped('product_uom_qty'))
        self.assertIn(10.0, picking.move_lines.mapped('product_uom_qty'))
        for move in picking.move_lines:
            self.assertEqual(
                move.purchase_line_id, self.purchase_01.order_line)

    def test_po_1_line_extra_move_without_linked_move_operation_ids(self):
        picking = self.purchase_01.picking_ids
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_uom_qty, 10)
        transfer_details = picking.do_enter_transfer_details()
        wizard_model = transfer_details.get('res_model')
        wizard_id = transfer_details.get('res_id')
        wizard_transfer = self.env[wizard_model].browse(wizard_id)
        self.assertEqual(len(wizard_transfer.item_ids), 1)
        self.assertEqual(wizard_transfer.item_ids.quantity, 10)
        wizard_transfer.item_ids[0].split_quantities()
        self.assertEqual(len(wizard_transfer.item_ids), 2)
        self.assertEqual(
            wizard_transfer.item_ids.mapped('quantity'), [9.0, 1.0])
        item_qty_1 = wizard_transfer.item_ids.filtered(
            lambda ln: ln.quantity == 1.0)
        self.assertEqual(len(item_qty_1), 1)
        item_qty_1.quantity = 32
        item_qty_9 = wizard_transfer.item_ids.filtered(
            lambda ln: ln.quantity == 9.0)
        self.assertEqual(len(item_qty_9), 1)
        item_qty_9.quantity = 25
        self.assertEqual(len(wizard_transfer.item_ids), 2)
        wizard_transfer.do_detailed_transfer()
        self.assertEqual(len(picking.move_lines), 3)
        self.assertIn(32.0, picking.move_lines.mapped('product_uom_qty'))
        self.assertIn(15.0, picking.move_lines.mapped('product_uom_qty'))
        self.assertIn(10.0, picking.move_lines.mapped('product_uom_qty'))
        for move in picking.move_lines:
            self.assertEqual(
                move.purchase_line_id, self.purchase_01.order_line)

    def test_po_several_lines_transfer_same_qty(self):
        picking = self.purchase_02.picking_ids
        self.assertEqual(len(picking.move_lines), 2)
        self.assertEqual(
            picking.move_lines.mapped('product_uom_qty'), [2.0, 8.0])
        transfer_details = picking.do_enter_transfer_details()
        wizard_model = transfer_details.get('res_model')
        wizard_id = transfer_details.get('res_id')
        wizard_transfer = self.env[wizard_model].browse(wizard_id)
        self.assertEqual(len(wizard_transfer.item_ids), 1)
        self.assertEqual(wizard_transfer.item_ids.quantity, 10)
        wizard_transfer.do_detailed_transfer()
        self.assertEqual(len(picking.move_lines), 2)
        self.assertIn(2.0, picking.move_lines.mapped('product_uom_qty'))
        self.assertIn(8.0, picking.move_lines.mapped('product_uom_qty'))
        self.assertEqual(
            picking.move_lines.mapped('purchase_line_id'),
            self.purchase_02.order_line)

    def test_po_several_lines_extra_move_with_linked_move_operation_ids(self):
        picking = self.purchase_02.picking_ids
        self.assertEqual(len(picking.move_lines), 2)
        self.assertEqual(
            picking.move_lines.mapped('product_uom_qty'), [2.0, 8.0])
        transfer_details = picking.do_enter_transfer_details()
        wizard_model = transfer_details.get('res_model')
        wizard_id = transfer_details.get('res_id')
        wizard_transfer = self.env[wizard_model].browse(wizard_id)
        self.assertEqual(len(wizard_transfer.item_ids), 1)
        self.assertEqual(wizard_transfer.item_ids.quantity, 10)
        wizard_transfer.item_ids[0].split_quantities()
        self.assertEqual(len(wizard_transfer.item_ids), 2)
        self.assertEqual(
            wizard_transfer.item_ids.mapped('quantity'), [9.0, 1.0])
        item_qty_1 = wizard_transfer.item_ids.filtered(
            lambda ln: ln.quantity == 1.0)
        self.assertEqual(len(item_qty_1), 1)
        item_qty_1.quantity = 10
        wizard_transfer.do_detailed_transfer()
        self.assertEqual(len(picking.move_lines), 3)
        self.assertIn(9.0, picking.move_lines.mapped('product_uom_qty'))
        self.assertIn(2.0, picking.move_lines.mapped('product_uom_qty'))
        self.assertIn(8.0, picking.move_lines.mapped('product_uom_qty'))
        for move in picking.move_lines:
            self.assertIn(move.purchase_line_id, self.purchase_02.order_line)

    def test_po_several_lines_extra_move_without_linked_move_operation_ids(
            self):
        picking = self.purchase_02.picking_ids
        self.assertEqual(len(picking.move_lines), 2)
        self.assertEqual(
            picking.move_lines.mapped('product_uom_qty'), [2.0, 8.0])
        transfer_details = picking.do_enter_transfer_details()
        wizard_model = transfer_details.get('res_model')
        wizard_id = transfer_details.get('res_id')
        wizard_transfer = self.env[wizard_model].browse(wizard_id)
        self.assertEqual(len(wizard_transfer.item_ids), 1)
        self.assertEqual(wizard_transfer.item_ids.quantity, 10)
        wizard_transfer.item_ids[0].split_quantities()
        self.assertEqual(len(wizard_transfer.item_ids), 2)
        self.assertEqual(
            wizard_transfer.item_ids.mapped('quantity'), [9.0, 1.0])
        item_qty_1 = wizard_transfer.item_ids.filtered(
            lambda ln: ln.quantity == 1.0)
        self.assertEqual(len(item_qty_1), 1)
        item_qty_1.quantity = 32
        item_qty_9 = wizard_transfer.item_ids.filtered(
            lambda ln: ln.quantity == 9.0)
        self.assertEqual(len(item_qty_9), 1)
        item_qty_9.quantity = 25
        self.assertEqual(len(wizard_transfer.item_ids), 2)
        wizard_transfer.do_detailed_transfer()
        self.assertEqual(len(picking.move_lines), 4)
        self.assertIn(32.0, picking.move_lines.mapped('product_uom_qty'))
        self.assertIn(15.0, picking.move_lines.mapped('product_uom_qty'))
        self.assertIn(2.0, picking.move_lines.mapped('product_uom_qty'))
        self.assertIn(8.0, picking.move_lines.mapped('product_uom_qty'))
        for move in picking.move_lines:
            self.assertIn(move.purchase_line_id, self.purchase_02.order_line)

    def test_po_1_line_transfer_and_return(self):
        picking = self.purchase_01.picking_ids
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_uom_qty, 10)
        transfer_details = picking.do_enter_transfer_details()
        wizard_model = transfer_details.get('res_model')
        wizard_id = transfer_details.get('res_id')
        wizard_transfer = self.env[wizard_model].browse(wizard_id)
        self.assertEqual(len(wizard_transfer.item_ids), 1)
        self.assertEqual(wizard_transfer.item_ids.quantity, 10)
        wizard_transfer.do_detailed_transfer()
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_uom_qty, 10.0)
        self.assertEqual(
            picking.move_lines.purchase_line_id,
            self.purchase_01.order_line)
        self.assertEqual(picking.invoice_state, '2binvoiced')
        invoice_ids = picking.action_invoice_create(
            journal_id=self.journal_purchase.id,
            group=False,
            type='in_invoice')
        self.assertEqual(len(invoice_ids), 1)
        invoice = self.env['account.invoice'].browse(invoice_ids)
        self.assertEqual(len(invoice.invoice_line), 1)
        self.assertEqual(invoice.invoice_line.quantity, 10)
        return_wiz = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids,
            active_id=picking.ids[0]
        ).create({})
        res = return_wiz._create_returns()[0]
        return_picking = self.env['stock.picking'].browse(res)
        self.assertEqual(len(self.purchase_01.picking_ids), 2)
        self.assertIn(return_picking, self.purchase_01.picking_ids)
        return_picking.action_assign()
        return_picking.do_transfer()
        self.assertEqual(len(return_picking.move_lines), 1)
        self.assertEqual(return_picking.move_lines.product_uom_qty, 10.0)
        self.assertEqual(
            return_picking.move_lines.purchase_line_id,
            self.purchase_01.order_line)
        self.assertEqual(return_picking.invoice_state, '2binvoiced')
        invoice_ids = return_picking.action_invoice_create(
            journal_id=self.journal_purchase_refund.id,
            group=False,
            type='in_refund')
        self.assertEqual(len(invoice_ids), 1)
        invoice = self.env['account.invoice'].browse(invoice_ids)
        self.assertEqual(len(invoice.invoice_line), 1)
        self.assertEqual(invoice.invoice_line.quantity, 10)

    def test_po_1_line_transfer_and_partial_return(self):
        picking = self.purchase_01.picking_ids
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_uom_qty, 10)
        transfer_details = picking.do_enter_transfer_details()
        wizard_model = transfer_details.get('res_model')
        wizard_id = transfer_details.get('res_id')
        wizard_transfer = self.env[wizard_model].browse(wizard_id)
        self.assertEqual(len(wizard_transfer.item_ids), 1)
        self.assertEqual(wizard_transfer.item_ids.quantity, 10)
        wizard_transfer.do_detailed_transfer()
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_uom_qty, 10.0)
        self.assertEqual(
            picking.move_lines.purchase_line_id,
            self.purchase_01.order_line)
        self.assertEqual(picking.invoice_state, '2binvoiced')
        invoice_ids = picking.action_invoice_create(
            journal_id=self.journal_purchase.id,
            group=False,
            type='in_invoice')
        self.assertEqual(len(invoice_ids), 1)
        invoice = self.env['account.invoice'].browse(invoice_ids)
        self.assertEqual(len(invoice.invoice_line), 1)
        self.assertEqual(invoice.invoice_line.quantity, 10)
        return_wiz = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids,
            active_id=picking.ids[0]
        ).create({})
        return_wiz.product_return_moves.quantity = 3
        res = return_wiz._create_returns()[0]
        return_picking = self.env['stock.picking'].browse(res)
        self.assertEqual(len(self.purchase_01.picking_ids), 2)
        self.assertIn(return_picking, self.purchase_01.picking_ids)
        return_picking.action_assign()
        return_picking.do_transfer()
        self.assertEqual(len(return_picking.move_lines), 1)
        self.assertEqual(return_picking.move_lines.product_uom_qty, 3.0)
        self.assertEqual(
            return_picking.move_lines.purchase_line_id,
            self.purchase_01.order_line)
        self.assertEqual(return_picking.invoice_state, '2binvoiced')
        invoice_ids = return_picking.action_invoice_create(
            journal_id=self.journal_purchase_refund.id,
            group=False,
            type='in_refund')
        self.assertEqual(len(invoice_ids), 1)
        invoice = self.env['account.invoice'].browse(invoice_ids)
        self.assertEqual(len(invoice.invoice_line), 1)
        self.assertEqual(invoice.invoice_line.quantity, 3)

    def test_po_1_line_extra_move_with_linked_move_operation_ids_ret(self):
        picking = self.purchase_01.picking_ids
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_uom_qty, 10)
        transfer_details = picking.do_enter_transfer_details()
        wizard_model = transfer_details.get('res_model')
        wizard_id = transfer_details.get('res_id')
        wizard_transfer = self.env[wizard_model].browse(wizard_id)
        self.assertEqual(len(wizard_transfer.item_ids), 1)
        self.assertEqual(wizard_transfer.item_ids.quantity, 10)
        wizard_transfer.item_ids[0].split_quantities()
        self.assertEqual(len(wizard_transfer.item_ids), 2)
        self.assertEqual(
            wizard_transfer.item_ids.mapped('quantity'), [9.0, 1.0])
        item_qty_1 = wizard_transfer.item_ids.filtered(
            lambda ln: ln.quantity == 1.0)
        self.assertEqual(len(item_qty_1), 1)
        item_qty_1.quantity = 10
        wizard_transfer.do_detailed_transfer()
        self.assertEqual(len(picking.move_lines), 2)
        self.assertIn(9.0, picking.move_lines.mapped('product_uom_qty'))
        self.assertIn(10.0, picking.move_lines.mapped('product_uom_qty'))
        for move in picking.move_lines:
            self.assertEqual(
                move.purchase_line_id, self.purchase_01.order_line)
        self.assertEqual(picking.invoice_state, '2binvoiced')
        invoice_ids = picking.action_invoice_create(
            journal_id=self.journal_purchase.id,
            group=False,
            type='in_invoice')
        self.assertEqual(len(invoice_ids), 1)
        invoice = self.env['account.invoice'].browse(invoice_ids)
        self.assertEqual(len(invoice.invoice_line), 2)
        self.assertIn(9.0, invoice.invoice_line.mapped('quantity'))
        self.assertIn(10.0, invoice.invoice_line.mapped('quantity'))
        return_wiz = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids,
            active_id=picking.ids[0]
        ).create({})
        res = return_wiz._create_returns()[0]
        return_picking = self.env['stock.picking'].browse(res)
        self.assertEqual(len(self.purchase_01.picking_ids), 2)
        self.assertIn(return_picking, self.purchase_01.picking_ids)
        return_picking.action_assign()
        return_picking.do_transfer()
        self.assertEqual(len(return_picking.move_lines), 2)
        self.assertIn(
            9.0, return_picking.move_lines.mapped('product_uom_qty'))
        self.assertIn(
            10.0, return_picking.move_lines.mapped('product_uom_qty'))
        for move_return in return_picking.move_lines:
            self.assertEqual(
                move_return.purchase_line_id, self.purchase_01.order_line)
        self.assertEqual(return_picking.invoice_state, '2binvoiced')
        invoice_ids = return_picking.action_invoice_create(
            journal_id=self.journal_purchase_refund.id,
            group=False,
            type='in_refund')
        self.assertEqual(len(invoice_ids), 1)
        invoice = self.env['account.invoice'].browse(invoice_ids)
        self.assertEqual(len(invoice.invoice_line), 2)
        self.assertIn(9.0, invoice.invoice_line.mapped('quantity'))
        self.assertIn(10.0, invoice.invoice_line.mapped('quantity'))

    def test_po_1_line_extra_move_without_linked_move_operation_ids_ret(self):
        picking = self.purchase_01.picking_ids
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_uom_qty, 10)
        transfer_details = picking.do_enter_transfer_details()
        wizard_model = transfer_details.get('res_model')
        wizard_id = transfer_details.get('res_id')
        wizard_transfer = self.env[wizard_model].browse(wizard_id)
        self.assertEqual(len(wizard_transfer.item_ids), 1)
        self.assertEqual(wizard_transfer.item_ids.quantity, 10)
        wizard_transfer.item_ids[0].split_quantities()
        self.assertEqual(len(wizard_transfer.item_ids), 2)
        self.assertEqual(
            wizard_transfer.item_ids.mapped('quantity'), [9.0, 1.0])
        item_qty_1 = wizard_transfer.item_ids.filtered(
            lambda ln: ln.quantity == 1.0)
        self.assertEqual(len(item_qty_1), 1)
        item_qty_1.quantity = 32
        item_qty_9 = wizard_transfer.item_ids.filtered(
            lambda ln: ln.quantity == 9.0)
        self.assertEqual(len(item_qty_9), 1)
        item_qty_9.quantity = 25
        self.assertEqual(len(wizard_transfer.item_ids), 2)
        wizard_transfer.do_detailed_transfer()
        self.assertEqual(len(picking.move_lines), 3)
        self.assertIn(32.0, picking.move_lines.mapped('product_uom_qty'))
        self.assertIn(15.0, picking.move_lines.mapped('product_uom_qty'))
        self.assertIn(10.0, picking.move_lines.mapped('product_uom_qty'))
        for move in picking.move_lines:
            self.assertEqual(
                move.purchase_line_id, self.purchase_01.order_line)
        self.assertEqual(picking.invoice_state, '2binvoiced')
        invoice_ids = picking.action_invoice_create(
            journal_id=self.journal_purchase.id,
            group=False,
            type='in_invoice')
        self.assertEqual(len(invoice_ids), 1)
        invoice = self.env['account.invoice'].browse(invoice_ids)
        self.assertEqual(len(invoice.invoice_line), 3)
        self.assertIn(32.0, invoice.invoice_line.mapped('quantity'))
        self.assertIn(15.0, invoice.invoice_line.mapped('quantity'))
        self.assertIn(10.0, invoice.invoice_line.mapped('quantity'))
        return_wiz = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids,
            active_id=picking.ids[0]
        ).create({})
        res = return_wiz._create_returns()[0]
        return_picking = self.env['stock.picking'].browse(res)
        self.assertEqual(len(self.purchase_01.picking_ids), 2)
        self.assertIn(return_picking, self.purchase_01.picking_ids)
        return_picking.action_assign()
        return_picking.do_transfer()
        self.assertEqual(len(return_picking.move_lines), 3)
        self.assertIn(
            32.0, return_picking.move_lines.mapped('product_uom_qty'))
        self.assertIn(
            15.0, return_picking.move_lines.mapped('product_uom_qty'))
        self.assertIn(
            10.0, return_picking.move_lines.mapped('product_uom_qty'))
        for move_return in return_picking.move_lines:
            self.assertEqual(
                move_return.purchase_line_id, self.purchase_01.order_line)
        self.assertEqual(return_picking.invoice_state, '2binvoiced')
        invoice_ids = return_picking.action_invoice_create(
            journal_id=self.journal_purchase_refund.id,
            group=False,
            type='in_refund')
        self.assertEqual(len(invoice_ids), 1)
        invoice = self.env['account.invoice'].browse(invoice_ids)
        self.assertEqual(len(invoice.invoice_line), 3)
        self.assertIn(32.0, invoice.invoice_line.mapped('quantity'))
        self.assertIn(15.0, invoice.invoice_line.mapped('quantity'))
        self.assertIn(10.0, invoice.invoice_line.mapped('quantity'))

    def test_so_1_line_transfer_same_qty(self):
        if not self.is_installed('sale'):
            pass
        self.update_stock(self.product_01, self.stock_location, 100)
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'pricelist_id': self.ref('product.list0'),
            'order_policy': 'picking',
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'product_uom_qty': 10,
                }),
            ]})
        sale.signal_workflow('order_confirm')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEqual(picking.invoice_state, '2binvoiced')
        picking.action_assign()
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_uom_qty, 10)
        transfer_details = picking.do_enter_transfer_details()
        wizard_model = transfer_details.get('res_model')
        wizard_id = transfer_details.get('res_id')
        wizard_transfer = self.env[wizard_model].browse(wizard_id)
        self.assertEqual(len(wizard_transfer.item_ids), 1)
        self.assertEqual(wizard_transfer.item_ids.quantity, 10)
        wizard_transfer.do_detailed_transfer()
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_uom_qty, 10.0)
        self.assertFalse(picking.move_lines.purchase_line_id)

    def test_so_1_line_extra_move_with_linked_move_operation_ids(self):
        if not self.is_installed('sale'):
            pass
        self.update_stock(self.product_01, self.stock_location, 100)
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'pricelist_id': self.ref('product.list0'),
            'order_policy': 'picking',
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'product_uom_qty': 10,
                }),
            ]})
        sale.signal_workflow('order_confirm')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEqual(picking.invoice_state, '2binvoiced')
        picking.action_assign()
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_uom_qty, 10)
        transfer_details = picking.do_enter_transfer_details()
        wizard_model = transfer_details.get('res_model')
        wizard_id = transfer_details.get('res_id')
        wizard_transfer = self.env[wizard_model].browse(wizard_id)
        self.assertEqual(len(wizard_transfer.item_ids), 1)
        self.assertEqual(wizard_transfer.item_ids.quantity, 10)
        wizard_transfer.item_ids[0].split_quantities()
        self.assertEqual(len(wizard_transfer.item_ids), 2)
        self.assertEqual(
            wizard_transfer.item_ids.mapped('quantity'), [9.0, 1.0])
        item_qty_1 = wizard_transfer.item_ids.filtered(
            lambda ln: ln.quantity == 1.0)
        self.assertEqual(len(item_qty_1), 1)
        item_qty_1.quantity = 10
        wizard_transfer.do_detailed_transfer()
        self.assertEqual(len(picking.move_lines), 2)
        self.assertIn(9.0, picking.move_lines.mapped('product_uom_qty'))
        self.assertIn(10.0, picking.move_lines.mapped('product_uom_qty'))
        for move in picking.move_lines:
            self.assertFalse(move.purchase_line_id)

    def test_so_1_line_extra_move_without_linked_move_operation_ids(self):
        self.update_stock(self.product_01, self.stock_location, 100)
        if not self.is_installed('sale'):
            pass
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'pricelist_id': self.ref('product.list0'),
            'order_policy': 'picking',
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'product_uom_qty': 10,
                }),
            ]})
        sale.signal_workflow('order_confirm')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEqual(picking.invoice_state, '2binvoiced')
        picking.action_assign()
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines.product_uom_qty, 10)
        transfer_details = picking.do_enter_transfer_details()
        wizard_model = transfer_details.get('res_model')
        wizard_id = transfer_details.get('res_id')
        wizard_transfer = self.env[wizard_model].browse(wizard_id)
        self.assertEqual(len(wizard_transfer.item_ids), 1)
        self.assertEqual(wizard_transfer.item_ids.quantity, 10)
        wizard_transfer.item_ids[0].split_quantities()
        self.assertEqual(len(wizard_transfer.item_ids), 2)
        self.assertEqual(
            wizard_transfer.item_ids.mapped('quantity'), [9.0, 1.0])
        item_qty_1 = wizard_transfer.item_ids.filtered(
            lambda ln: ln.quantity == 1.0)
        self.assertEqual(len(item_qty_1), 1)
        item_qty_1.quantity = 32
        item_qty_9 = wizard_transfer.item_ids.filtered(
            lambda ln: ln.quantity == 9.0)
        self.assertEqual(len(item_qty_9), 1)
        item_qty_9.quantity = 25
        self.assertEqual(len(wizard_transfer.item_ids), 2)
        wizard_transfer.do_detailed_transfer()
        self.assertEqual(len(picking.move_lines), 3)
        self.assertIn(32.0, picking.move_lines.mapped('product_uom_qty'))
        self.assertIn(15.0, picking.move_lines.mapped('product_uom_qty'))
        self.assertIn(10.0, picking.move_lines.mapped('product_uom_qty'))
        for move in picking.move_lines:
            self.assertFalse(move.purchase_line_id)
