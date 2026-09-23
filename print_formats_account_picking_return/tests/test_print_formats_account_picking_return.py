###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import timedelta

from odoo.tests import common


class TestPrintFormatsAccountPickingReturn(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.uom_unit = self.env.ref('uom.product_uom_unit')
        self.product_01_ip_delivery = self.env['product.product'].create({
            'name': 'Product 01',
            'type': 'product',
            'standard_price': 10,
            'list_price': 15,
            'uom_id': self.uom_unit.id,
            'uom_po_id': self.uom_unit.id,
            'invoice_policy': 'delivery',
        })
        self.product_02_ip_delivery = self.env['product.product'].create({
            'name': 'Product 02',
            'type': 'product',
            'standard_price': 5,
            'list_price': 10,
            'uom_id': self.uom_unit.id,
            'uom_po_id': self.uom_unit.id,
            'invoice_policy': 'delivery',
        })
        self.product_03_ip_order = self.env['product.product'].create({
            'name': 'Product 03',
            'type': 'product',
            'standard_price': 3,
            'list_price': 10,
            'uom_id': self.uom_unit.id,
            'uom_po_id': self.uom_unit.id,
            'invoice_policy': 'order',
        })
        self.product_04_ip_order = self.env['product.product'].create({
            'name': 'Product 04',
            'type': 'product',
            'standard_price': 4,
            'list_price': 10,
            'uom_id': self.uom_unit.id,
            'uom_po_id': self.uom_unit.id,
            'invoice_policy': 'order',
        })
        self.product_05_ip_delivery = self.env['product.product'].create({
            'name': 'Product 05',
            'type': 'product',
            'standard_price': 7,
            'list_price': 12,
            'uom_id': self.uom_unit.id,
            'uom_po_id': self.uom_unit.id,
            'invoice_policy': 'delivery',
        })
        self.partner_01 = self.env['res.partner'].create({
            'name': 'Partner 01',
        })
        self.tax_15 = self.env['account.tax'].create({
            'name': 'TAX 15%',
            'amount_type': 'percent',
            'type_tax_use': 'purchase',
            'amount': 15.0,
        })
        self.location = self.env.ref('stock.stock_location_stock')
        self.update_qty_on_hand(self.product_01_ip_delivery, self.location, 10)
        self.update_qty_on_hand(self.product_02_ip_delivery, self.location, 10)
        self.update_qty_on_hand(self.product_03_ip_order, self.location, 10)
        self.update_qty_on_hand(self.product_04_ip_order, self.location, 10)
        self.update_qty_on_hand(self.product_05_ip_delivery, self.location, 10)

    def update_qty_on_hand(self, product, location, new_qty):
        wizard = self.env['stock.change.product.qty'].create({
            'product_id': product.id,
            'new_quantity': new_qty,
            'location_id': location.id,
        })
        wizard.change_product_qty()

    def create_sale_order(self, partner, products, qty):
        order_lines = []
        for product in products:
            order_line = {
                'product_id': product.id,
                'product_uom_qty': qty,
                'price_unit': product.list_price,
                'product_uom': product.uom_id.id,
            }
            order_lines.append((0, 0, order_line))
        return self.env['sale.order'].create({
            'partner_id': partner.id,
            'partner_invoice_id': partner.id,
            'order_line': order_lines,
        })

    def test_print_format_account_products_ip_delivery_group_by_picking(self):
        sale_order = self.create_sale_order(
            self.partner_01,
            [self.product_01_ip_delivery, self.product_02_ip_delivery], 2)
        sale_order.company_id.invoice_report_group_by = 'picking'
        sale_order.action_confirm()
        picking = sale_order.picking_ids
        picking.action_assign()
        picking.move_lines[0].quantity_done = 2
        picking.move_lines[1].quantity_done = 2
        picking.button_validate()
        return_wizard = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids,
            active_id=picking.id,
        ).create({
            'product_return_moves': [
                (0, 0, {
                    'product_id': picking.move_lines[0].product_id.id,
                    'quantity': 2,
                    'move_id': picking.move_lines[0].id,
                    'uom_id': picking.move_lines[0].product_uom.id,
                    'to_refund': True,
                }),
                (0, 0, {
                    'product_id': picking.move_lines[1].product_id.id,
                    'quantity': 1,
                    'move_id': picking.move_lines[1].id,
                    'uom_id': picking.move_lines[1].product_uom.id,
                    'to_refund': True,
                }),
            ],
        })
        return_picking = self.env['stock.picking'].browse(
            return_wizard.create_returns()['res_id'])
        return_picking.action_assign()
        return_picking.move_lines[0].quantity_done = 2
        return_picking.move_lines[1].quantity_done = 1
        return_picking.button_validate()
        sale_order.action_invoice_create()
        invoice = sale_order.invoice_ids
        invoice.write({
            'create_date': (return_picking.create_date + timedelta(seconds=10))
        })
        parser_model = self.env['report.account.report_invoice_base']
        report_data = parser_model.get_lines_grouped(invoice)
        calculated_price_subtotal = 0
        calculated_price_total = 0
        for line in report_data:
            so_data_report = line['picking'].sale_id
            self.assertEqual(so_data_report, sale_order)
            calculated_price_subtotal += line['price_subtotal']
            calculated_price_total += line['price_total']
        self.assertEqual(calculated_price_subtotal, 10.0)
        self.assertEqual(calculated_price_total, 11.5)

    def test_print_format_account_products_ip_delivery_without_group_by(self):
        sale_order = self.create_sale_order(
            self.partner_01,
            [self.product_01_ip_delivery, self.product_02_ip_delivery], 2)
        sale_order.company_id.invoice_report_group_by = False
        sale_order.action_confirm()
        picking = sale_order.picking_ids
        picking.action_assign()
        picking.move_lines[0].quantity_done = 2
        picking.move_lines[1].quantity_done = 2
        picking.button_validate()
        return_wizard = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids,
            active_id=picking.id,
        ).create({
            'product_return_moves': [
                (0, 0, {
                    'product_id': picking.move_lines[0].product_id.id,
                    'quantity': 2,
                    'move_id': picking.move_lines[0].id,
                    'uom_id': picking.move_lines[0].product_uom.id,
                    'to_refund': True,
                }),
                (0, 0, {
                    'product_id': picking.move_lines[1].product_id.id,
                    'quantity': 1,
                    'move_id': picking.move_lines[1].id,
                    'uom_id': picking.move_lines[1].product_uom.id,
                    'to_refund': True,
                }),
            ],
        })
        return_picking = self.env['stock.picking'].browse(
            return_wizard.create_returns()['res_id'])
        return_picking.action_assign()
        return_picking.move_lines[0].quantity_done = 2
        return_picking.move_lines[1].quantity_done = 1
        return_picking.button_validate()
        sale_order.action_invoice_create()
        invoice = sale_order.invoice_ids
        invoice.write({
            'create_date': (
                return_picking.create_date + timedelta(seconds=10))
        })
        parser_model = self.env['report.account.report_invoice_base']
        report_data = parser_model.get_lines_grouped(invoice)
        self.assertEqual(len(report_data), 4)
        calculated_price_subtotal = 0
        calculated_price_total = 0
        for line in report_data:
            self.assertEqual(line['picking'], False)
            so_data_report = line['move'].sale_line_id.order_id
            self.assertEqual(so_data_report, sale_order)
            calculated_price_subtotal += line['price_subtotal']
            calculated_price_total += line['price_total']
        self.assertEqual(calculated_price_subtotal, 10.0)
        self.assertEqual(calculated_price_total, 11.5)

    def test_print_format_account_products_ip_order_group_by_picking(self):
        sale_order = self.create_sale_order(
            self.partner_01,
            [self.product_03_ip_order, self.product_04_ip_order], 2)
        sale_order.company_id.invoice_report_group_by = 'picking'
        sale_order.action_confirm()
        picking = sale_order.picking_ids
        picking.action_assign()
        picking.move_lines[0].quantity_done = 2
        picking.move_lines[1].quantity_done = 2
        picking.button_validate()
        return_wizard = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids,
            active_id=picking.id,
        ).create({
            'product_return_moves': [
                (0, 0, {
                    'product_id': picking.move_lines[0].product_id.id,
                    'quantity': 2,
                    'move_id': picking.move_lines[0].id,
                    'uom_id': picking.move_lines[0].product_uom.id,
                    'to_refund': True,
                }),
                (0, 0, {
                    'product_id': picking.move_lines[1].product_id.id,
                    'quantity': 1,
                    'move_id': picking.move_lines[1].id,
                    'uom_id': picking.move_lines[1].product_uom.id,
                    'to_refund': True,
                }),
            ],
        })
        return_picking = self.env['stock.picking'].browse(
            return_wizard.create_returns()['res_id'])
        return_picking.action_assign()
        return_picking.move_lines[0].quantity_done = 2
        return_picking.move_lines[1].quantity_done = 1
        return_picking.button_validate()
        sale_order.action_invoice_create()
        self.assertEqual(len(sale_order.picking_ids), 2)
        invoice = sale_order.invoice_ids
        invoice.write({
            'create_date': (return_picking.create_date + timedelta(seconds=10))
        })
        parser_model = self.env['report.account.report_invoice_base']
        report_data = parser_model.get_lines_grouped(invoice)
        calculated_price_subtotal = 0
        calculated_price_total = 0
        self.assertEqual(len(report_data), 6)
        self.assertEqual(report_data[0]['picking'], False)
        self.assertEqual(report_data[0]['move'].product_id,
                         self.product_03_ip_order)
        self.assertEqual(report_data[0]['quantity'], (
            report_data[0]['move'].sale_line_id.product_uom_qty
            - report_data[0]['move'].sale_line_id.qty_delivered))
        self.assertEqual(report_data[1]['picking'], False)
        self.assertEqual(report_data[1]['move'].product_id,
                         self.product_04_ip_order)
        self.assertEqual(report_data[1]['quantity'], (
            report_data[1]['move'].sale_line_id.product_uom_qty
            - report_data[1]['move'].sale_line_id.qty_delivered))
        for line in report_data:
            if line['picking']:
                self.assertIn(line['picking'], sale_order.picking_ids)
            so_data_report = line['move'].sale_line_id.order_id
            self.assertEqual(so_data_report, sale_order)
            calculated_price_subtotal += line['price_subtotal']
            calculated_price_total += line['price_total']
        self.assertEqual(calculated_price_subtotal, 40.0)
        self.assertEqual(calculated_price_total, 46.0)

    def test_print_format_account_products_ip_order_without_group_by(self):
        sale_order = self.create_sale_order(
            self.partner_01,
            [self.product_03_ip_order, self.product_04_ip_order], 2)
        sale_order.company_id.invoice_report_group_by = False
        sale_order.action_confirm()
        picking = sale_order.picking_ids
        picking.action_assign()
        picking.move_lines[0].quantity_done = 2
        picking.move_lines[1].quantity_done = 2
        picking.button_validate()
        return_wizard = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids,
            active_id=picking.id,
        ).create({
            'product_return_moves': [
                (0, 0, {
                    'product_id': picking.move_lines[0].product_id.id,
                    'quantity': 2,
                    'move_id': picking.move_lines[0].id,
                    'uom_id': picking.move_lines[0].product_uom.id,
                    'to_refund': True,
                }),
                (0, 0, {
                    'product_id': picking.move_lines[1].product_id.id,
                    'quantity': 1,
                    'move_id': picking.move_lines[1].id,
                    'uom_id': picking.move_lines[1].product_uom.id,
                    'to_refund': True,
                }),
            ],
        })
        return_picking = self.env['stock.picking'].browse(
            return_wizard.create_returns()['res_id'])
        return_picking.action_assign()
        return_picking.move_lines[0].quantity_done = 2
        return_picking.move_lines[1].quantity_done = 1
        return_picking.button_validate()
        sale_order.action_invoice_create()
        self.assertEqual(len(sale_order.picking_ids), 2)
        invoice = sale_order.invoice_ids
        invoice.write({
            'create_date': (return_picking.create_date + timedelta(seconds=10))
        })
        parser_model = self.env['report.account.report_invoice_base']
        report_data = parser_model.get_lines_grouped(invoice)
        calculated_price_subtotal = 0
        calculated_price_total = 0
        self.assertEqual(len(report_data), 6)
        self.assertEqual(report_data[0]['move'].product_id,
                         self.product_03_ip_order)
        self.assertEqual(report_data[0]['quantity'], (
            report_data[0]['move'].sale_line_id.product_uom_qty
            - report_data[0]['move'].sale_line_id.qty_delivered))
        self.assertEqual(report_data[1]['move'].product_id,
                         self.product_04_ip_order)
        self.assertEqual(report_data[1]['quantity'], (
            report_data[1]['move'].sale_line_id.product_uom_qty
            - report_data[1]['move'].sale_line_id.qty_delivered))
        for line in report_data:
            self.assertEqual(line['picking'], False)
            so_data_report = line['move'].sale_line_id.order_id
            self.assertEqual(so_data_report, sale_order)
            calculated_price_subtotal += line['price_subtotal']
            calculated_price_total += line['price_total']
        self.assertEqual(calculated_price_subtotal, 40.0)
        self.assertEqual(calculated_price_total, 46.0)

    def test_print_invoice_twice_the_same_sale_order_after_delivered(self):
        sale_order = self.create_sale_order(
            self.partner_01,
            [self.product_01_ip_delivery,
             self.product_02_ip_delivery,
             self.product_05_ip_delivery], 2)
        sale_order.company_id.invoice_report_group_by = 'picking'
        sale_order.action_confirm()
        picking = sale_order.picking_ids
        picking.action_assign()
        picking.move_lines[0].quantity_done = 2
        picking.move_lines[1].quantity_done = 2
        res = picking.button_validate()
        self.env['stock.backorder.confirmation'].browse(res['res_id']).process()
        return_wizard = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids,
            active_id=picking.id,
        ).create({
            'product_return_moves': [
                (0, 0, {
                    'product_id': picking.move_lines[0].product_id.id,
                    'quantity': 2,
                    'move_id': picking.move_lines[0].id,
                    'uom_id': picking.move_lines[0].product_uom.id,
                    'to_refund': True,
                }),
                (0, 0, {
                    'product_id': picking.move_lines[1].product_id.id,
                    'quantity': 1,
                    'move_id': picking.move_lines[1].id,
                    'uom_id': picking.move_lines[1].product_uom.id,
                    'to_refund': True,
                }),
            ],
        })
        return_picking = self.env['stock.picking'].browse(
            return_wizard.create_returns()['res_id'])
        return_picking.action_assign()
        return_picking.move_lines[0].quantity_done = 2
        return_picking.move_lines[1].quantity_done = 1
        return_picking.button_validate()
        sale_order.action_invoice_create()
        invoice = sale_order.invoice_ids
        invoice.write({
            'create_date': (
                return_picking.create_date + timedelta(seconds=10))
        })
        parser_model = self.env['report.account.report_invoice_base']
        report_data = parser_model.get_lines_grouped(invoice)
        self.assertEqual(len(report_data), 4)
        calculated_price_subtotal = 0
        calculated_price_total = 0
        for line in report_data:
            so_data_report = line['picking'].sale_id
            self.assertEqual(so_data_report, sale_order)
            calculated_price_subtotal += line['price_subtotal']
            calculated_price_total += line['price_total']
        self.assertEqual(calculated_price_subtotal, 10.0)
        self.assertEqual(calculated_price_total, 11.5)
        picking_to_deliver = sale_order.picking_ids.filtered(
            lambda p: p.state != 'done')
        picking_to_deliver.action_assign()
        picking_to_deliver.move_lines.quantity_done = 2
        picking_to_deliver.button_validate()
        new_invoice_id = sale_order.action_invoice_create()[0]
        new_invoice = self.env['account.invoice'].browse(new_invoice_id)
        invoice.write({
            'create_date': (return_picking.create_date + timedelta(seconds=15))
        })
        report_data = parser_model.get_lines_grouped(new_invoice)
        self.assertEqual(len(report_data), 1)
        calculated_price_subtotal = 0
        calculated_price_total = 0
        so_data_report = report_data[0]['picking'].sale_id
        self.assertEqual(so_data_report, sale_order)
        calculated_price_subtotal += report_data[0]['price_subtotal']
        calculated_price_total += report_data[0]['price_total']
        self.assertEqual(calculated_price_subtotal, 24.0)
        self.assertEqual(calculated_price_total, 27.6)

    def test_print_format_account_products_ip_order_and_delivery_group_by_picking(self):
        sale_order = self.create_sale_order(
            self.partner_01,
            [self.product_01_ip_delivery, self.product_04_ip_order], 2)
        sale_order.company_id.invoice_report_group_by = 'picking'
        sale_order.action_confirm()
        picking = sale_order.picking_ids
        picking.action_assign()
        picking.move_lines[0].quantity_done = 2
        picking.move_lines[1].quantity_done = 1
        res = picking.button_validate()
        self.env['stock.backorder.confirmation'].browse(res['res_id']).process()
        return_wizard = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids,
            active_id=picking.id,
        ).create({
            'product_return_moves': [
                (0, 0, {
                    'product_id': picking.move_lines[0].product_id.id,
                    'quantity': 1,
                    'move_id': picking.move_lines[0].id,
                    'uom_id': picking.move_lines[0].product_uom.id,
                    'to_refund': True,
                }),
            ],
        })
        return_picking = self.env['stock.picking'].browse(
            return_wizard.create_returns()['res_id'])
        return_picking.action_assign()
        return_picking.move_lines[0].quantity_done = 1
        return_picking.button_validate()
        sale_order.action_invoice_create()
        self.assertEqual(len(sale_order.picking_ids), 3)
        invoice = sale_order.invoice_ids
        invoice.write({
            'create_date': (return_picking.create_date + timedelta(seconds=10))
        })
        parser_model = self.env['report.account.report_invoice_base']
        report_data = parser_model.get_lines_grouped(invoice)
        self.assertEqual(len(report_data), 4)
        calculated_price_subtotal = 0
        calculated_price_total = 0
        self.assertEqual(report_data[0]['picking'], False)
        self.assertEqual(
            report_data[0]['move'].product_id, self.product_04_ip_order)
        self.assertEqual(
            report_data[0]['quantity'], (
                report_data[0]['move'].sale_line_id.product_uom_qty
                - report_data[0]['move'].sale_line_id.qty_delivered))
        for line in report_data:
            if line['picking']:
                self.assertIn(line['picking'], sale_order.picking_ids)
            so_data_report = line['move'].sale_line_id.order_id
            self.assertEqual(so_data_report, sale_order)
            calculated_price_subtotal += line['price_subtotal']
            calculated_price_total += line['price_total']
        self.assertEqual(calculated_price_subtotal, 35.0)
        self.assertEqual(calculated_price_total, 40.25)

    def test_print_format_account_manual_create(self):
        invoice = self.env['account.invoice'].create({
            'partner_id': self.partner_01.id,
            'type': 'out_invoice',
        })
        invoice_line = self.env['account.invoice.line'].create({
            'name': 'Line 01',
            'account_id': self.env.ref('account.data_account_type_revenue').id,
            'invoice_id': invoice.id,
            'product_id': self.product_01_ip_delivery.id,
            'quantity': 2,
            'price_unit': self.product_01_ip_delivery.list_price,
            'uom_id': self.product_01_ip_delivery.uom_id.id,
        })
        parser_model = self.env['report.account.report_invoice_base']
        report_data = parser_model.get_lines_grouped(invoice)
        self.assertEqual(len(report_data), 1)
        self.assertEqual(report_data[0]['picking'], False)
        self.assertEqual(report_data[0]['line'], invoice_line)
        self.assertEqual(report_data[0]['quantity'], 2)
        self.assertEqual(report_data[0]['price_unit'], 15.0)
        self.assertEqual(report_data[0]['price_subtotal'], 30.0)
        self.assertEqual(report_data[0]['price_total'], 30.0)

    def test_print_format_account_change_prices_in_invoice(self):
        sale_order = self.create_sale_order(
            self.partner_01,
            [self.product_01_ip_delivery, self.product_02_ip_delivery], 2)
        sale_order.company_id.invoice_report_group_by = 'picking'
        sale_order.action_confirm()
        picking = sale_order.picking_ids
        picking.action_assign()
        picking.move_lines[0].quantity_done = 2
        picking.move_lines[1].quantity_done = 2
        picking.button_validate()
        return_wizard = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids,
            active_id=picking.id,
        ).create({
            'product_return_moves': [
                (0, 0, {
                    'product_id': picking.move_lines[0].product_id.id,
                    'quantity': 1,
                    'move_id': picking.move_lines[0].id,
                    'uom_id': picking.move_lines[0].product_uom.id,
                    'to_refund': True,
                }),
                (0, 0, {
                    'product_id': picking.move_lines[1].product_id.id,
                    'quantity': 1,
                    'move_id': picking.move_lines[1].id,
                    'uom_id': picking.move_lines[1].product_uom.id,
                    'to_refund': True,
                }),
            ],
        })
        return_picking = self.env['stock.picking'].browse(
            return_wizard.create_returns()['res_id'])
        return_picking.action_assign()
        return_picking.move_lines[0].quantity_done = 1
        return_picking.move_lines[1].quantity_done = 1
        return_picking.button_validate()
        sale_order.action_invoice_create()
        invoice = sale_order.invoice_ids
        invoice.write({
            'create_date': (return_picking.create_date + timedelta(seconds=10))
        })
        self.assertEqual(invoice.amount_untaxed, 25.0)
        self.assertEqual(invoice.amount_tax, 3.75)
        self.assertEqual(invoice.amount_total, 28.75)
        for invoice_line in invoice.invoice_line_ids:
            invoice_line.price_unit = 3.0
            invoice._onchange_invoice_line_ids()
        self.assertEqual(invoice.amount_untaxed, 6.0)
        self.assertEqual(invoice.amount_tax, 0.9)
        self.assertEqual(invoice.amount_total, 6.90)
        parser_model = self.env['report.account.report_invoice_base']
        report_data = parser_model.get_lines_grouped(invoice)
        calculated_price_subtotal = 0
        calculated_price_total = 0
        for line in report_data:
            so_data_report = line['picking'].sale_id
            self.assertEqual(so_data_report, sale_order)
            calculated_price_subtotal += line['price_subtotal']
            calculated_price_total += line['price_total']
        self.assertEqual(calculated_price_subtotal, 6.0)
        self.assertEqual(round(calculated_price_total, 2), 6.90)

    def test_print_format_account_change_discount_in_invoice(self):
        sale_order = self.create_sale_order(
            self.partner_01,
            [self.product_01_ip_delivery, self.product_02_ip_delivery], 2)
        sale_order.company_id.invoice_report_group_by = 'picking'
        sale_order.action_confirm()
        picking = sale_order.picking_ids
        picking.action_assign()
        picking.move_lines[0].quantity_done = 2
        picking.move_lines[1].quantity_done = 2
        picking.button_validate()
        return_wizard = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids,
            active_id=picking.id,
        ).create({
            'product_return_moves': [
                (0, 0, {
                    'product_id': picking.move_lines[0].product_id.id,
                    'quantity': 1,
                    'move_id': picking.move_lines[0].id,
                    'uom_id': picking.move_lines[0].product_uom.id,
                    'to_refund': True,
                }),
                (0, 0, {
                    'product_id': picking.move_lines[1].product_id.id,
                    'quantity': 1,
                    'move_id': picking.move_lines[1].id,
                    'uom_id': picking.move_lines[1].product_uom.id,
                    'to_refund': True,
                }),
            ],
        })
        return_picking = self.env['stock.picking'].browse(
            return_wizard.create_returns()['res_id'])
        return_picking.action_assign()
        return_picking.move_lines[0].quantity_done = 1
        return_picking.move_lines[1].quantity_done = 1
        return_picking.button_validate()
        sale_order.action_invoice_create()
        invoice = sale_order.invoice_ids
        invoice.write({
            'create_date': (return_picking.create_date + timedelta(seconds=10))
        })
        invoice.invoice_line_ids.write({
            'invoice_line_tax_ids': [(6, 0, [self.tax_15.id])],
        })
        self.assertEqual(invoice.amount_untaxed, 25.0)
        self.assertEqual(invoice.amount_tax, 3.75)
        self.assertEqual(invoice.amount_total, 28.75)
        for invoice_line in invoice.invoice_line_ids:
            invoice_line.discount = 50.00
            invoice._onchange_invoice_line_ids()
        self.assertEqual(invoice.amount_untaxed, 12.5)
        self.assertEqual(invoice.amount_tax, 1.88)
        self.assertEqual(invoice.amount_total, 14.38)
        parser_model = self.env['report.account.report_invoice_base']
        report_data = parser_model.get_lines_grouped(invoice)
        calculated_price_subtotal = 0
        calculated_price_total = 0
        for line in report_data:
            so_data_report = line['picking'].sale_id
            self.assertEqual(so_data_report, sale_order)
            calculated_price_subtotal += line['price_subtotal']
            calculated_price_total += line['price_total']
        self.assertEqual(calculated_price_subtotal, 12.5)
        self.assertEqual(round(calculated_price_total, 2), 14.38)

    def test_print_format_account_invoice_line_qty_zero(self):
        sale_order = self.create_sale_order(
            self.partner_01,
            [self.product_01_ip_delivery, self.product_02_ip_delivery], 2)
        sale_order.company_id.invoice_report_group_by = 'picking'
        sale_order.action_confirm()
        picking = sale_order.picking_ids
        picking.action_assign()
        picking.move_lines[0].quantity_done = 2
        picking.move_lines[1].quantity_done = 2
        picking.button_validate()
        sale_order.action_invoice_create()
        invoice = sale_order.invoice_ids
        invoice.invoice_line_ids[0].quantity = 0
        parser_model = self.env['report.account.report_invoice_base']
        report_data = parser_model.get_lines_grouped(invoice)
        self.assertEqual(len(report_data), 3)
        self.assertEqual(report_data[0]['picking'], False)
        self.assertEqual(report_data[0]['quantity'], -2)
        self.assertEqual(report_data[0]['price_unit'], 0)
        self.assertEqual(report_data[0]['price_subtotal'], 0)
        self.assertEqual(report_data[0]['price_total'], 0)

    def test_cancel_a_picking_of_sale_and_change_uom_qty_zero(self):
        sale_order = self.create_sale_order(
            self.partner_01,
            [self.product_01_ip_delivery], 2)
        sale_order.company_id.invoice_report_group_by = 'picking'
        sale_order.action_confirm()
        picking = sale_order.picking_ids
        self.assertEqual(len(picking), 1)
        picking.action_cancel()
        sale_order.order_line.product_uom_qty = 0
        self.env['sale.order.line'].create({
            'order_id': sale_order.id,
            'product_id': self.product_02_ip_delivery.id,
            'product_uom_qty': 4,
            'price_unit': self.product_02_ip_delivery.list_price,
        })
        self.assertEqual(len(sale_order.picking_ids), 2)
        picking_assigned = sale_order.picking_ids.filtered(
            lambda p: p.state != 'cancel')
        self.assertEqual(len(picking_assigned), 1)
        picking_assigned.move_lines[0].quantity_done = 4
        picking_assigned.button_validate()
        sale_order.action_invoice_create()
        invoice = sale_order.invoice_ids
        parser_model = self.env['report.account.report_invoice_base']
        report_data = parser_model.get_lines_grouped(invoice)
        self.assertEqual(len(report_data), 1)
