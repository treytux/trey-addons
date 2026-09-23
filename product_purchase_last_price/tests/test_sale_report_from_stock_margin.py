###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestSaleReportFromStockMargin(TransactionCase):

    def setUp(self):
        super().setUp()
        self.stock_wh = self.env.ref('stock.warehouse0')
        self.customer_loc = self.env.ref('stock.stock_location_customers')
        type_revenue = self.env.ref('account.data_account_type_revenue')
        type_payable = self.env.ref('account.data_account_type_payable')
        self.account_customer = self.env['account.account'].create({
            'name': 'Customer',
            'code': 'XX_430',
            'user_type_id': type_payable.id,
            'reconcile': True,
        })
        self.account_supplier = self.env['account.account'].create({
            'name': 'Supplier',
            'code': 'XX_400',
            'user_type_id': type_revenue.id,
            'reconcile': True,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'property_account_receivable_id': self.account_customer.id,
            'property_account_payable_id': self.account_supplier.id,
        })
        self.pricelist = self.env.ref('product.list0')
        self.pricelist.currency_id = self.env.user.company_id.currency_id.id
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Physical product',
            'standard_price': 10,
            'list_price': 100,
            'invoice_policy': 'delivery',
        })
        purchase = self.create_purchase()
        self.create_purchase_line(purchase, self.product, price=50)
        purchase.button_confirm()
        picking = purchase.picking_ids
        picking.action_assign()
        picking.move_line_ids.write({
            'qty_done': 2,
        })
        picking.button_validate()

    def create_purchase(self):
        return self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })

    def create_purchase_line(self, purchase, product, price=False, discount=False):
        line_obj = self.env['purchase.order.line']
        line = line_obj.new({
            'order_id': purchase.id,
            'name': product.name,
            'product_id': product.id,
            'product_uom': product.uom_id.id,
        })
        line.onchange_product_id()
        line = line_obj.create(line_obj._convert_to_write(line._cache))
        data = {
            'product_qty': 2,
        }
        if price:
            data.update({
                'price_unit': price,
            })
        if discount:
            data.update({
                'discount': discount,
            })
        line.write(data)
        return line

    def create_sale_order(self, partner, partner_shipping, warehouse, qty):
        order_line = {
            'name': self.product.name,
            'product_id': self.product.id,
            'product_uom_qty': qty,
            'product_uom': self.product.uom_id.id,
            'price_unit': self.product.list_price,
        }
        return self.env['sale.order'].create({
            'partner_id': partner.id,
            'partner_invoice_id': partner.id,
            'partner_shipping_id': partner_shipping.id,
            'order_line': [(0, 0, order_line)],
            'warehouse_id': warehouse.id,
            'pricelist_id': self.pricelist.id,
        })

    def create_sale_and_picking(self, qty):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': qty,
                }),
            ]
        })
        sale.action_confirm()
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        return sale

    def test_check_report(self):
        old_report = self.env['sale.report.from_stock_move'].search([])
        self.create_sale_and_picking(1)
        self.create_sale_and_picking(1)
        self.create_sale_and_picking(1)
        new_report = self.env['sale.report.from_stock_move'].search([])
        self.assertEqual(len(old_report) + 3, len(new_report))

    def test_sales_orders_to_customer_with_return(self):
        old_report = self.env['sale.report.from_stock_move'].search([])
        sale_01 = self.create_sale_and_picking(10)
        done_pickings = sale_01.picking_ids.filtered(
            lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_pickings.ids,
            active_id=done_pickings.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.quantity = 1.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.quantity_done = 1
        return_pick.action_done()
        sale_02 = self.create_sale_and_picking(10)
        new_report = self.env['sale.report.from_stock_move'].search([])
        self.assertEqual(len(old_report) + 3, len(new_report))
        sale_01_rows = new_report.filtered(lambda r: r.order_id == sale_01)
        self.assertEqual(len(sale_01_rows), 2)
        sale_01_out = new_report.filtered(
            lambda r: r.order_id == sale_01
            and r.location_id == self.stock_wh.lot_stock_id
            and r.location_dest_id == self.customer_loc)
        self.assertEqual(len(sale_01_out), 1)
        self.assertEqual(sale_01_out.product_id, self.product)
        self.assertEqual(sale_01_out.product_uom_qty, 10)
        self.assertEqual(sale_01_out.operation_total, 1000)
        self.assertEqual(sale_01_out.margin, 500)
        sale_01_in = new_report.filtered(
            lambda r: r.order_id == sale_01
            and r.location_id == self.customer_loc
            and r.location_dest_id == self.stock_wh.lot_stock_id)
        self.assertEqual(len(sale_01_in), 1)
        self.assertEqual(sale_01_in.product_id, self.product)
        self.assertEqual(sale_01_in.product_uom_qty, -1)
        self.assertEqual(sale_01_in.operation_total, -100)
        self.assertEqual(sale_01_in.margin, -50)
        sale_02_out = new_report.filtered(lambda r: r.order_id == sale_02)
        self.assertEqual(len(sale_02_out), 1)
        self.assertEqual(sale_02_out.product_id, self.product)
        self.assertEqual(sale_02_out.product_uom_qty, 10)
        self.assertEqual(sale_02_out.operation_total, 1000)
        self.assertEqual(sale_02_out.margin, 500)
        margin = sale_01_out.margin + sale_01_in.margin + sale_02_out.margin
        self.assertEqual(margin, 950)

    def test_margin_uses_zero_purchase_last_price(self):
        sale = self.create_sale_and_picking(10)
        sale.order_line.write({
            'purchase_last_price': 0.0,
        })
        report_line = self.env['sale.report.from_stock_move'].search([
            ('order_id', '=', sale.id),
            ('location_id', '=', self.stock_wh.lot_stock_id.id),
            ('location_dest_id', '=', self.customer_loc.id),
        ], limit=1)
        self.assertEqual(report_line.purchase_last_price, 0.0)
        self.assertEqual(report_line.operation_total, 1000)
        self.assertEqual(report_line.margin, 1000)
