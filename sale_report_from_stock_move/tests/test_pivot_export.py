###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import io
import json
import urllib.parse

import pandas as pd
from odoo.addons.sale_report_from_stock_move.controllers.main import \
    CustomTableExporter
from odoo.exceptions import UserError
from odoo.tests.common import HttpCase


class TestPivotExport(HttpCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer',
        })
        category_all = self.env.ref('product.product_category_all')
        self.product1 = self.env['product.product'].create({
            'name': 'Real Test Product',
            'type': 'product',
            'categ_id': category_all.id,
            'list_price': 300.0,
            'standard_price': 50.0,
        })
        wizard_p1 = self.env['stock.change.product.qty'].create({
            'product_id': self.product1.id,
            'new_quantity': 100.0,
        })
        wizard_p1.change_product_qty()
        self.order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product1.id,
                'product_uom_qty': 10.0,
                'price_unit': 300.0,
            })]
        })
        self.order.action_confirm()
        picking = self.order.picking_ids[0]
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()

    def test_excel_with_real_database_flow_pandas(self):
        self.authenticate('admin', 'admin')
        report_line = self.env['sale.report.from_stock_move'].search([
            ('product_id', '=', self.product1.id),
        ], limit=1)
        self.assertTrue(report_line)
        js_data = {
            'title': 'Real Pandas Analysis',
            'nbr_measures': 2,
            'technical_measures': ['price_unit', 'margin'],
            'headers': [[{
                'title': 'Total',
                'width': 1,
                'height': 1,
            }]],
            'measure_row': [
                {'measure': 'Price', 'is_bold': False},
                {'measure': 'Margin', 'is_bold': False}
            ],
            'rows': [{
                'title': self.product1.name,
                'values': [
                    {'value': report_line.price_unit, 'is_bold': False},
                    {'value': report_line.margin, 'is_bold': False}
                ]
            }]
        }
        query = urllib.parse.urlencode({
            'data': json.dumps(js_data),
            'token': 'test',
        })
        response = self.url_open('/web/pivot/export_custom_xls?' + query)
        self.assertEqual(response.status_code, 200)
        df = pd.read_excel(io.BytesIO(response.content), engine='xlrd', header=None)
        all_values = [str(val) for val in df.values.flatten()]
        self.assertIn(self.product1.name, all_values)
        self.assertTrue(any('300' in val for val in all_values))

    def test_missing_measures_raises_correct_error(self):
        bad_js_data = {
            'title': 'Error Test',
            'technical_measures': ['product_uom_qty'],
            'headers': [[{
                'title': 'Total',
                'width': 1, 'height': 1,
            }]],
            'measure_row': [{
                'measure': 'Qty',
                'is_bold': False,
            }],
            'rows': [],
        }
        controller = CustomTableExporter()
        with self.assertRaises(UserError) as error_catcher:
            controller.export_xls(data=json.dumps(bad_js_data), token='test')
        self.assertEqual(
            error_catcher.exception.args[0],
            'Price and Margin columns are missing in the pivot view.')

    def test_real_margin_mathematical_verification(self):
        self.authenticate('admin', 'admin')
        report_line = self.env['sale.report.from_stock_move'].search([
            ('product_id', '=', self.product1.id),
        ], limit=1)
        p_unit = report_line.price_unit
        operation_total = report_line.operation_total
        expected_margin = (
            1 - ((p_unit / operation_total) * 100)
            if operation_total else 0.0
        )
        js_data = {
            'title': 'Real Mathematical Validation',
            'nbr_measures': 2,
            'technical_measures': ['price_unit', 'operation_total'],
            'headers': [[{'title': 'Total', 'width': 1, 'height': 1}]],
            'measure_row': [
                {'measure': 'Price', 'is_bold': False},
                {'measure': 'Price Operation', 'is_bold': False},
                {'measure': '% Margin', 'is_bold': True}
            ],
            'rows': [{
                'title': self.product1.name,
                'values': [
                    {'value': p_unit, 'is_bold': False},
                    {'value': operation_total, 'is_bold': False},
                    {'value': '=IF(C4=0,0,1-(B4/C4)*100)', 'is_bold': True}
                ]
            }]
        }
        query = urllib.parse.urlencode({
            'data': json.dumps(js_data),
            'token': 'test',
        })
        response = self.url_open('/web/pivot/export_custom_xls?' + query)
        df = pd.read_excel(
            io.BytesIO(response.content), engine='xlrd', header=None)
        product_row = df[df[0] == self.product1.name]
        excel_base_val = pd.to_numeric(product_row.iloc[0, 1])
        excel_operation_val = pd.to_numeric(product_row.iloc[0, 2])
        self.assertEqual(excel_base_val, p_unit)
        self.assertEqual(excel_operation_val, operation_total)
        math_result = 1 - ((excel_base_val / excel_operation_val) * 100)
        self.assertAlmostEqual(math_result, expected_margin, places=2)
