###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common
from xlrd import open_workbook


class TestReportPurchaseOrderXlsx(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.buy_route = self.env.ref('purchase_stock.route_warehouse0_buy')
        self.mto_route = self.env.ref('stock.route_warehouse0_mto')
        self.team = self.env['crm.team'].create({
            'name': 'Team test',
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test',
            'standard_price': 10,
            'list_price': 100,
        })
        self.product_route = self.env['product.product'].create({
            'type': 'product',
            'name': 'Product route test',
            'standard_price': 10,
            'list_price': 100,
            'route_ids': [(6, 0, [self.buy_route.id, self.mto_route.id])],
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.customer_01 = self.env['res.partner'].create({
            'name': 'Customer test 1',
            'customer': True,
            'city': 'Granada',
            'zip': '18008',
            'phone': '999887766',
            'street': 'Street test',
            'street2': 'Nº test',
        })
        self.env['product.supplierinfo'].create({
            'name': self.customer_01.id,
            'product_tmpl_id': self.product_route.product_tmpl_id.id,
            'price': 80,
        })
        self.purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        line_obj = self.env['purchase.order.line']
        line = line_obj.new({
            'order_id': self.purchase.id,
            'product_id': self.product.id,
            'price_unit': 100,
            'quantity': 1
        })
        line.onchange_product_id()
        line_obj.create(line_obj._convert_to_write(line._cache))
        self.purchase.button_confirm()
        self.report_name = 'report_purchase_order_xlsx.purchase_order_xlsx'

    def test_purchase_order_line_with_sale_order_id_export_xlsx(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.customer_01.id,
            'team_id': self.team.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_route.id,
                    'price_unit': self.product_route.list_price,
                    'product_uom_qty': 1,
                    'route_id': self.mto_route.id,
                })
            ]
        })
        self.assertEqual(sale.team_id, self.team)
        sale.action_confirm()
        purchase_order = self.env['purchase.order'].search([
            ('origin', 'ilike', sale.name),
        ])
        self.assertEqual(len(purchase_order), 1)
        self.assertEqual(len(purchase_order.order_line), 1)
        self.assertEqual(
            purchase_order.order_line[0].product_id.id, self.product_route.id)
        self.assertEqual(
            purchase_order.order_line[0].move_dest_ids[0].sale_line_id.id,
            sale.order_line[0].id)
        self.assertIn(sale.name, purchase_order.origin)
        purchase_order.order_line[0].sale_order_id = sale.id
        self.assertEqual(purchase_order.order_line[0].sale_order_id, sale)
        report_xlsx = self.env.ref(self.report_name).render(purchase_order.ids)
        self.assertGreaterEqual(len(report_xlsx[0]), 1)
        self.assertEqual(report_xlsx[1], 'xlsx')
        wb = open_workbook(file_contents=report_xlsx[0])
        sheet = wb.sheet_by_index(0)
        self.assertEqual(sheet.cell(1, 0).value, purchase_order.name)
        self.assertEqual(sheet.cell(1, 1).value, sale.team_id.id)
        self.assertEqual(sheet.cell(1, 2).value, sale.partner_id.name)
        self.assertEqual(
            sheet.cell(1, 3).value,
            sale.partner_id.street + ' ' + sale.partner_id.street2)
        self.assertEqual(sheet.cell(1, 4).value, sale.partner_id.zip)
        self.assertEqual(sheet.cell(1, 5).value, sale.partner_id.city)
        self.assertEqual(sheet.cell(1, 6).value, sale.partner_id.phone)

    def test_link_purchase_order_from_route_export_xlsx(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.customer_01.id,
            'team_id': self.team.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_route.id,
                    'price_unit': self.product_route.list_price,
                    'product_uom_qty': 1,
                    'route_id': self.mto_route.id,
                })
            ]
        })
        self.assertEqual(sale.team_id, self.team)
        sale.action_confirm()
        purchase_order = self.env['purchase.order'].search([
            ('origin', 'ilike', sale.name),
        ])
        self.assertEqual(len(purchase_order), 1)
        self.assertEqual(len(purchase_order.order_line), 1)
        self.assertEqual(
            purchase_order.order_line[0].product_id.id, self.product_route.id)
        self.assertEqual(
            purchase_order.order_line[0].move_dest_ids[0].sale_line_id.id,
            sale.order_line[0].id)
        self.assertIn(sale.name, purchase_order.origin)
        report_xlsx = self.env.ref(self.report_name).render(purchase_order.ids)
        self.assertGreaterEqual(len(report_xlsx[0]), 1)
        self.assertEqual(report_xlsx[1], 'xlsx')
        wb = open_workbook(file_contents=report_xlsx[0])
        sheet = wb.sheet_by_index(0)
        self.assertEqual(sheet.cell(1, 0).value, purchase_order.name)
        self.assertEqual(sheet.cell(1, 1).value, sale.team_id.id)
        self.assertEqual(sheet.cell(1, 2).value, sale.partner_id.name)
        self.assertEqual(
            sheet.cell(1, 3).value,
            sale.partner_id.street + ' ' + sale.partner_id.street2)
        self.assertEqual(sheet.cell(1, 4).value, sale.partner_id.zip)
        self.assertEqual(sheet.cell(1, 5).value, sale.partner_id.city)
        self.assertEqual(sheet.cell(1, 6).value, sale.partner_id.phone)

    def XXXtest_purchase_order_export_to_xlsx(self):
        report_xlsx = self.env.ref(self.report_name).render(self.purchase.ids)
        self.assertGreaterEqual(len(report_xlsx[0]), 1)
        self.assertEqual(report_xlsx[1], 'xlsx')
        wb = open_workbook(file_contents=report_xlsx[0])
        sheet = wb.sheet_by_index(0)
        self.assertEqual(sheet.cell(0, 0).value, 'Nº Purchase')
        self.assertEqual(sheet.cell(0, 1).value, 'Reference')
        self.assertEqual(sheet.cell(0, 2).value, 'Partner')
        self.assertEqual(sheet.cell(0, 3).value, 'Street')
        self.assertEqual(sheet.cell(0, 4).value, 'Zip')
        self.assertEqual(sheet.cell(0, 5).value, 'City')
        self.assertEqual(sheet.cell(0, 6).value, 'Phone')
        self.assertEqual(sheet.cell(0, 7).value, 'Date order')
        self.assertEqual(sheet.cell(0, 8).value, 'Barcode')
        self.assertEqual(sheet.cell(0, 9).value, 'Default code')
        self.assertEqual(sheet.cell(0, 10).value, 'Product')
        self.assertEqual(sheet.cell(0, 11).value, 'Product quantity')
        self.assertEqual(sheet.cell(0, 12).value, 'Download date')
        self.assertEqual(sheet.cell(1, 0).value, self.purchase.name)
        self.assertEqual(sheet.cell(1, 10).value, self.product.name)
        self.assertEqual(
            sheet.cell(1, 11).value, self.purchase.order_line[0].product_qty)
