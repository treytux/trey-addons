import re

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('stock_picking_line_section', 'post_install', '-at_install')
class TestStockPickingLineSection(TransactionCase):
    def setUp(self):
        super().setUp()
        if 'sales_amount_limit' in self.env.user._fields:
            self.env.user.sales_amount_limit = 19
        if 'sales_discount_limit' in self.env.user._fields:
            self.env.user.sales_discount_limit = 100.0
        partner_vals = {'name': 'Test partner'}
        if 'default_delivery_block' in self.env['res.partner']._fields:
            partner_vals['default_delivery_block'] = False
        self.partner = self.env['res.partner'].create(partner_vals)
        self.product_sectioned = self.env['product.product'].create({
            'name': 'Sectioned product',
            'type': 'consu',
            'company_id': False,
        })
        self.product_second = self.env['product.product'].create({
            'name': 'Second product',
            'type': 'consu',
            'company_id': False,
        })

    def _create_sale_order_and_picking(self, with_section=True):
        order_lines = []
        if with_section:
            order_lines.append(
                (0, 0, {
                    'display_type': 'line_section',
                    'name': 'WAREHOUSE',
                    'sequence': 1,
                }),
            )
        order_lines.append(
            (0, 0, {
                'product_id': self.product_sectioned.id,
                'name': self.product_sectioned.display_name,
                'product_uom_qty': 1.0,
                'product_uom': self.product_sectioned.uom_id.id,
                'price_unit': 10.0,
                'sequence': 2,
            }))
        return self._create_order_and_picking(order_lines)

    def _create_multi_section_sale_order_and_picking(self):
        order_lines = [
            (0, 0, {
                'display_type': 'line_section',
                'name': 'WAREHOUSE',
                'sequence': 1,
            }),
            (0, 0, {
                'product_id': self.product_sectioned.id,
                'name': self.product_sectioned.display_name,
                'product_uom_qty': 1.0,
                'product_uom': self.product_sectioned.uom_id.id,
                'price_unit': 10.0,
                'sequence': 2,
            }),
            (0, 0, {
                'display_type': 'line_section',
                'name': 'OUTBOUND',
                'sequence': 3,
            }),
            (0, 0, {
                'product_id': self.product_second.id,
                'name': self.product_second.display_name,
                'product_uom_qty': 2.0,
                'product_uom': self.product_second.uom_id.id,
                'price_unit': 20.0,
                'sequence': 4,
            }),
        ]
        return self._create_order_and_picking(order_lines)

    def _create_order_and_picking(self, order_lines):
        order_vals = {
            'partner_id': self.partner.id,
            'warehouse_id': self.env.ref('stock.warehouse0').id,
            'order_line': order_lines,
        }
        if 'manual_delivery' in self.env['sale.order']._fields:
            order_vals['manual_delivery'] = False
        if 'delivery_block_id' in self.env['sale.order']._fields:
            order_vals['delivery_block_id'] = False
        order = self.env['sale.order'].create(order_vals)
        order.action_confirm()
        if (
            'delivery_block_id' in order._fields
            and order.delivery_block_id
                and hasattr(order, 'action_remove_delivery_block')):
            order.action_remove_delivery_block()
        picking = order.picking_ids[:1]
        debug_info = [
            f'state={order.state}',
            f'picking_count={len(order.picking_ids)}',
            f'line_count={len(order.order_line)}',
        ]
        if 'delivery_block_id' in order._fields:
            debug_info.append(
                f'delivery_block_id={order.delivery_block_id.id}')
        self.assertTrue(picking, ', '.join(debug_info))
        move = picking.move_ids[:1]
        self.assertTrue(move)
        return order, picking, move

    def _set_picking_done(self, picking):
        picking.action_confirm()
        picking.action_assign()
        for stock_move in picking.move_ids:
            stock_move.quantity_done = stock_move.product_uom_qty
        picking.button_validate()

    def _render_deliveryslip_html(self, picking):
        result = self.env['ir.actions.report']._render_qweb_html(
            'stock.report_deliveryslip', picking.ids, False)
        html = result[0]
        return html.decode() if isinstance(html, bytes) else str(html)

    def _assert_section_header_present(self, html, section_name):
        section_row_pattern = re.compile(
            rf'<tr[^>]*class=["\'][^"\']*o_line_section[^"\']*'
            rf'["\'][^>]*>.*?{re.escape(section_name)}.*?</tr>',
            re.S)
        self.assertRegex(html, section_row_pattern)

    def _assert_ordered_rows(self, html, row_expectations):
        rows = re.findall(r'<tr[^>]*>.*?</tr>', html, flags=re.S)
        current_index = 0
        for row_type, row_label in row_expectations:
            found_index = None
            for row_index in range(current_index, len(rows)):
                row = rows[row_index]
                if row_type == 'section':
                    if 'o_line_section' in row and row_label in row:
                        found_index = row_index
                        break
                elif row_type == 'line':
                    if 'o_line_section' not in row and row_label in row:
                        found_index = row_index
                        break
            self.assertIsNotNone(found_index)
            current_index = found_index + 1

    def test_move_sale_section_name(self):
        _order, picking, move = self._create_sale_order_and_picking(
            with_section=True)
        section_name = picking._get_move_sale_section_name(move=move)
        self.assertEqual(section_name, 'WAREHOUSE')

    def test_move_sale_section_name_without_section(self):
        _order, picking, move = self._create_sale_order_and_picking(
            with_section=False)
        section_name = picking._get_move_sale_section_name(move=move)
        self.assertFalse(section_name)

    def test_report_deliveryslip_grouped_section_before_done(self):
        _order, picking, _move = self._create_sale_order_and_picking(
            with_section=True)
        html = self._render_deliveryslip_html(picking)
        self._assert_section_header_present(html, 'WAREHOUSE')
        self._assert_ordered_rows(
            html,
            [
                ('section', 'WAREHOUSE'),
                ('line', 'Sectioned product'),
            ])

    def test_report_deliveryslip_grouped_section_done_aggregated_lines(self):
        _order, picking, _move = self._create_sale_order_and_picking(
            with_section=True)
        self._set_picking_done(picking)
        html = self._render_deliveryslip_html(picking)
        self._assert_section_header_present(html, 'WAREHOUSE')
        self._assert_ordered_rows(
            html,
            [
                ('section', 'WAREHOUSE'),
                ('line', 'Sectioned product'),
            ])

    def test_report_deliveryslip_before_done_without_section(self):
        _order, picking, _move = self._create_sale_order_and_picking(
            with_section=False)
        html = self._render_deliveryslip_html(picking)
        self.assertNotIn('o_line_section', html)
        self.assertIn('Sectioned product', html)

    def test_report_deliveryslip_done_aggregated_lines_without_section(self):
        _order, picking, _move = self._create_sale_order_and_picking(
            with_section=False)
        self._set_picking_done(picking)
        html = self._render_deliveryslip_html(picking)
        self.assertNotIn('o_line_section', html)
        self.assertIn('Sectioned product', html)

    def test_report_deliveryslip_multi_section_order_done_aggregated(self):
        _order, picking, _move = (
            self._create_multi_section_sale_order_and_picking())
        self._set_picking_done(picking)
        html = self._render_deliveryslip_html(picking)
        self._assert_section_header_present(html, 'WAREHOUSE')
        self._assert_section_header_present(html, 'OUTBOUND')
        self._assert_ordered_rows(
            html, [
                ('section', 'WAREHOUSE'),
                ('line', 'Sectioned product'),
                ('section', 'OUTBOUND'),
                ('line', 'Second product'),
            ])
