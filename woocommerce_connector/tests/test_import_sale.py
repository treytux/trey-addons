###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json
import os

from odoo.addons.woocommerce_connector.tests import test_common as common
from odoo.exceptions import UserError


class TestImportSale(common.TestCommon):

    def get_filepath(self, fname):
        return os.path.join(os.path.dirname(__file__), 'files', fname)

    def test_import_sale(self):
        with open(self.get_filepath('sale_7231.json')) as fp:
            json_data = json.loads(fp.read())
        sale_obj = self.env['sale.order']
        with self.assertRaises(UserError) as exception:
            sale = sale_obj.woo_sync_import_record(
                self.website, json_data['order'], json_data['refund'])
        self.assertIn('Taxs not mapped', exception.exception.name)
        self.assertIn('launch a sync operation and', exception.exception.name)
        map_tax = self.env['website.woo.mapp.tax'].create({
            'name': 'EU VAT (ES) 21%',
            'website_id': self.website.id,
            'woo_id': 37,
            'woo_rate': 21.0,
        })
        with self.assertRaises(UserError) as exception:
            sale = sale_obj.woo_sync_import_record(
                self.website, json_data['order'], json_data['refund'])
        self.assertIn('Taxs not mapped', exception.exception.name)
        self.assertIn('Please go to', exception.exception.name)
        tax_group_taxes = self.env.ref('account.tax_group_taxes')
        tax = self.env['account.tax'].create({
            'name': '[OdooWooConn] Tax for sale 21%',
            'type_tax_use': 'sale',
            'tax_group_id': tax_group_taxes.id,
            'amount_type': 'percent',
            'amount': 21.0,
        })
        map_tax.tax_id = tax.id
        sale = sale_obj.with_context(debug=True).woo_sync_import_record(
            self.website, json_data['order'], json_data['refund'])
        self.assertEqual(len(sale), 1)
        self.assertEqual(len(sale.order_line), 5)
        self.assertEqual(
            len(sale.order_line.filtered(lambda ln: ln.is_delivery)), 1)
        self.assertEqual(
            len(sale.order_line.filtered(lambda ln: ln.display_type)), 1)
        product_obj = self.env['product.product']
        product_1 = product_obj.create({
            'type': 'product',
            'company_id': False,
            'name': '[OdooWooConn] PRODUCT 1',
            'default_code': 'PRO-1',
            'standard_price': 10,
            'list_price': 129.95,
            'website_id': self.website.id,
            'website_published': True,
        })
        product_2 = product_obj.create({
            'type': 'product',
            'company_id': False,
            'name': '[OdooWooConn] PRODUCT 2',
            'default_code': 'PRO-2',
            'standard_price': 10,
            'list_price': 849.95,
            'website_id': self.website.id,
            'website_published': True,
        })
        product_3 = product_obj.create({
            'type': 'product',
            'company_id': False,
            'name': '[OdooWooConn] PRODUCT 3',
            'default_code': 'PRO-3',
            'standard_price': 10,
            'list_price': 299.95,
            'website_id': self.website.id,
            'website_published': True,
        })
        sale = sale_obj.woo_sync_import_record(
            self.website, json_data['order'], json_data['refund'])
        line_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == product_1)
        self.assertTrue(line_1)
        self.assertIn('Refund', line_1.name)
        self.assertAlmostEqual(line_1.price_unit, 123.46, places=2)
        self.assertEqual(line_1.product_uom_qty, 0)
        self.assertEqual(line_1.price_subtotal, 0)
        self.assertIn(product_2, sale.order_line.mapped('product_id'))
        self.assertIn(product_3, sale.order_line.mapped('product_id'))
        self.assertEqual(sale.amount_total, 1329.0)
