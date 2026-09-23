###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestPrintOptionsSale(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Print Options Sale Test Partner',
        })
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })

    def test_action_print_options_sale_opens_wizard(self):
        action = self.sale_order.action_print_options_sale()
        self.assertEqual(action['res_model'], 'wiz.print.options.sale')
        self.assertEqual(action['target'], 'new')

    def test_button_print_with_prices(self):
        wiz = self.env['wiz.print.options.sale'].with_context(
            active_ids=self.sale_order.ids).create({
                'print_option': 'with_prices',
            })
        action = wiz.button_print()
        self.assertEqual(action['report_name'], 'sale.report_saleorder')
        self.assertEqual(action['data']['print_option'], 'with_prices')
        self.assertEqual(
            action['data']['order_ids'], self.sale_order.ids)

    def test_button_print_without_prices(self):
        wiz = self.env['wiz.print.options.sale'].with_context(
            active_ids=self.sale_order.ids).create({
                'print_option': 'without_prices',
            })
        action = wiz.button_print()
        self.assertEqual(action['report_name'], 'sale.report_saleorder')
        self.assertEqual(action['data']['print_option'], 'without_prices')
        self.assertEqual(
            action['data']['order_ids'], self.sale_order.ids)

    def test_report_values_from_data_without_docids(self):
        report_model = self.env['report.sale.report_saleorder']
        values = report_model._get_report_values(None, data={
            'print_option': 'without_prices',
            'order_ids': self.sale_order.ids,
        })
        self.assertEqual(values['docs'], self.sale_order)
        self.assertEqual(values['print_option'], 'without_prices')

    def test_report_values_from_docids(self):
        report_model = self.env['report.sale.report_saleorder']
        values = report_model._get_report_values(
            self.sale_order.ids, data={})
        self.assertEqual(values['docs'], self.sale_order)

    def test_report_html_renders_order_without_docids(self):
        report = self.env.ref('sale.action_report_saleorder')
        html = report._render_qweb_html(
            'sale.report_saleorder', None, data={
                'print_option': 'with_prices',
                'order_ids': self.sale_order.ids,
            })[0]
        self.assertIn(self.sale_order.name, html.decode())
