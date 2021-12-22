###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import logging
import os
from datetime import datetime, timedelta

import requests
from odoo import _, fields, tools
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

_log = logging.getLogger(__name__)


class TestBeezupExporter(TransactionCase):

    def setUp(self):
        super().setUp()
        (self.fname_us,
         self.fname_us_lock,
         self.fname_update_stock_us,
         self.fname_update_stock_us_lock) = self.generate_lang_files('en_US')
        (self.fname_es,
         self.fname_es_lock,
         self.fname_update_stock_es,
         self.fname_update_stock_es_lock) = self.generate_lang_files('es_ES')
        (self.fname_pt,
         self.fname_pt_lock,
         self.fname_update_stock_pt,
         self.fname_update_stock_pt_lock) = self.generate_lang_files('pt_PT')
        self.stock_wh = self.env.ref('stock.warehouse0')
        self.public_pricelist = self.env.ref('product.list0')
        self.env.user.company_id.beezup_pricelist_id = self.public_pricelist.id
        self.product1 = self.env['product.product'].create({
            'name': 'Test product 1',
            'type': 'product',
            'default_code': '20056',
            'barcode': '8435502834914',
            'standard_price': 70,
            'list_price': 100,
            'export_to_beezup': True,
            'weight': 3,
        })
        self.product2 = self.env['product.product'].create({
            'name': 'Test product 2',
            'type': 'product',
            'default_code': '22222',
            'barcode': '7501031311309',
            'standard_price': 150,
            'list_price': 200,
            'export_to_beezup': True,
            'weight': 4,
        })
        self.product3 = self.env['product.product'].create({
            'name': 'Test product 3',
            'type': 'product',
            'default_code': '88888',
            'barcode': '4317784094610',
            'standard_price': 80,
            'list_price': 300,
            'export_to_beezup': True,
            'weight': 5,
        })

    def generate_lang_files(self, lang):
        path = tools.config.filestore(self.env.cr.dbname)
        return (
            '%s/beezup_%s.csv' % (path, lang),
            '%s/beezup_%s.lock' % (path, lang),
            '%s/beezup_%s_update_stock.csv' % (path, lang),
            '%s/beezup_%s_update_stock.lock' % (path, lang)
        )

    def remove_files(self, fnames):
        for fname in fnames:
            if os.path.exists(fname):
                os.remove(fname)

    def force_future_write_date(self, record):
        record.write({
            'write_date': fields.Datetime.now() + timedelta(minutes=5),
        })

    def images_get(self, url):
        images = []
        warns = []
        if not url:
            return images, warns
        try:
            response = requests.get(url)
            images.append(base64.b64encode(response.content))
        except Exception:
            warns.append(_('Url image not found for %s.') % url)
        return images, warns

    def update_qty_on_hand(self, product, location, new_qty):
        wizard = self.env['stock.change.product.qty'].create({
            'product_id': product.id,
            'new_quantity': new_qty,
            'location_id': location.id,
        })
        wizard.change_product_qty()
        self.assertEquals(product.with_context(
            location=location.id).qty_available, new_qty)

    def check_beezup_generate_company(self, test, company_id=None):
        product_obj = self.env['product.product']
        if test == 'type_1':
            fname, content = self.product1.beezup_generate_file(
                'standard', company_id=company_id)
            self.assertEquals(fname, self.fname_us)
            self.assertTrue(os.path.exists(self.fname_us))
            self.assertFalse(os.path.exists(self.fname_us_lock))
            self.assertEquals(len(content), 1)
            for _index, row in content.iterrows():
                self.assertEquals(row['id'], self.product1.id)
                self.assertEquals(row['name'], 'Test product 1')
                self.assertEquals(row['barcode'], '8435502834914')
                self.assertEquals(row['customer_price'], 100)
                self.assertEquals(row['weight'], 3)
                self.assertEquals(row['qty_available'], 0)
                self.assertEquals(row['stock_web'], 0)
                self.assertEquals(row['default_code'], '20056')
            content_last = self.product1.beezup_get_file_last('standard')
            self.assertEquals(len(content_last), 1)
            for _index, row in content_last.iterrows():
                self.assertEquals(row['id'], self.product1.id)
                self.assertEquals(row['name'], 'Test product 1')
                self.assertEquals(row['barcode'], '8435502834914')
                self.assertEquals(row['customer_price'], 100)
                self.assertEquals(row['weight'], 3)
                self.assertEquals(row['qty_available'], 0)
                self.assertEquals(row['stock_web'], 0)
                self.assertEquals(row['default_code'], '20056')
        elif test == 'type_2':
            fname, content = product_obj.beezup_generate_file(
                'standard', company_id=company_id)
            self.assertEquals(fname, self.fname_us)
            self.assertTrue(os.path.exists(self.fname_us))
            self.assertFalse(os.path.exists(self.fname_us_lock))
            self.assertEquals(len(content), 1)
            for _index, row in content.iterrows():
                self.assertEquals(row['id'], self.product1.id)
                self.assertEquals(row['name'], 'Test product 1')
                self.assertEquals(row['barcode'], '8435502834914')
                self.assertEquals(row['customer_price'], 100)
                self.assertEquals(row['weight'], 3)
                self.assertEquals(row['qty_available'], 0)
                self.assertEquals(row['stock_web'], 0)
                self.assertEquals(row['default_code'], '20056')
            fname2, content2 = product_obj.beezup_generate_file(
                'standard', company_id=company_id)
            self.assertEquals(fname2, self.fname_us)
            self.assertTrue(os.path.exists(self.fname_us))
            self.assertFalse(os.path.exists(self.fname_us_lock))
            self.assertEquals(len(content2), 1)
            for _index, row in content2.iterrows():
                self.assertEquals(row['id'], self.product1.id)
                self.assertEquals(row['name'], 'Test product 1')
                self.assertEquals(row['barcode'], '8435502834914')
                self.assertEquals(row['customer_price'], 100)
                self.assertEquals(row['weight'], 3)
                self.assertEquals(row['qty_available'], 0)
                self.assertEquals(row['stock_web'], 0)
                self.assertEquals(row['default_code'], '20056')
            file_date_write1 = datetime.fromtimestamp(os.path.getmtime(fname))
            file_date_write2 = datetime.fromtimestamp(os.path.getmtime(fname2))
            self.assertEquals(file_date_write1, file_date_write2)
        elif test == 'type_3':
            fname, content = product_obj.beezup_generate_file(
                'standard', company_id=company_id)
            self.assertEquals(fname, self.fname_us)
            self.assertTrue(os.path.exists(self.fname_us))
            self.assertFalse(os.path.exists(self.fname_us_lock))
            self.assertEquals(len(content), 2)
            for _index, row in content.iterrows():
                if row['id'] == self.product1.id:
                    self.assertEquals(row['name'], 'Test product 1')
                    self.assertEquals(row['barcode'], '8435502834914')
                    self.assertEquals(row['customer_price'], 100)
                    self.assertEquals(row['weight'], 3)
                    self.assertEquals(row['qty_available'], 0)
                    self.assertEquals(row['stock_web'], 0)
                    self.assertEquals(row['default_code'], '20056')
                elif row['id'] == self.product2.id:
                    self.assertEquals(row['name'], 'Test product 2')
                    self.assertEquals(row['barcode'], '7501031311309')
                    self.assertEquals(row['customer_price'], 200)
                    self.assertEquals(row['weight'], 4)
                    self.assertEquals(row['qty_available'], 0)
                    self.assertEquals(row['stock_web'], 0)
                    self.assertEquals(row['default_code'], '22222')
            self.product2.default_code = '33333'
            self.force_future_write_date(self.product2)
            self.product3.export_to_beezup = True
            self.force_future_write_date(self.product3)
            fname, content = product_obj.beezup_generate_file(
                'standard', company_id=company_id)
            self.assertEquals(fname, self.fname_us)
            self.assertTrue(os.path.exists(self.fname_us))
            self.assertFalse(os.path.exists(self.fname_us_lock))
            self.assertEquals(len(content), 3)
            for _index, row in content.iterrows():
                if row['id'] == self.product1.id:
                    self.assertEquals(row['name'], 'Test product 1')
                    self.assertEquals(row['barcode'], '8435502834914')
                    self.assertEquals(row['customer_price'], 100)
                    self.assertEquals(row['weight'], 3)
                    self.assertEquals(row['qty_available'], 0)
                    self.assertEquals(row['stock_web'], 0)
                    self.assertEquals(row['default_code'], '20056')
                elif row['id'] == self.product2.id:
                    self.assertEquals(row['name'], 'Test product 2')
                    self.assertEquals(row['barcode'], '7501031311309')
                    self.assertEquals(row['customer_price'], 200)
                    self.assertEquals(row['weight'], 4)
                    self.assertEquals(row['qty_available'], 0)
                    self.assertEquals(row['stock_web'], 0)
                    self.assertEquals(row['default_code'], '33333')
                elif row['id'] == self.product3.id:
                    self.assertEquals(row['name'], 'Test product 3')
                    self.assertEquals(row['barcode'], '4317784094610')
                    self.assertEquals(row['customer_price'], 300)
                    self.assertEquals(row['weight'], 5)
                    self.assertEquals(row['qty_available'], 0)
                    self.assertEquals(row['stock_web'], 0)
                    self.assertEquals(row['default_code'], '88888')
        elif test == 'type_4':
            fname, content = product_obj.beezup_generate_file(
                'standard', company_id=company_id)
            self.assertEquals(fname, self.fname_us)
            self.assertTrue(os.path.exists(self.fname_us))
            self.assertFalse(os.path.exists(self.fname_us_lock))
            self.assertEquals(len(content), 2)
            for _index, row in content.iterrows():
                if row['id'] == self.product1.id:
                    self.assertEquals(row['name'], 'Test product 1')
                    self.assertEquals(row['barcode'], '8435502834914')
                    self.assertEquals(row['customer_price'], 100)
                    self.assertEquals(row['weight'], 3)
                    self.assertEquals(row['qty_available'], 0)
                    self.assertEquals(row['stock_web'], 0)
                    self.assertEquals(row['default_code'], '20056')
                elif row['id'] == self.product2.id:
                    self.assertEquals(row['name'], 'Test product 2')
                    self.assertEquals(row['barcode'], '7501031311309')
                    self.assertEquals(row['customer_price'], 200)
                    self.assertEquals(row['weight'], 4)
                    self.assertEquals(row['qty_available'], 0)
                    self.assertEquals(row['stock_web'], 0)
                    self.assertEquals(row['default_code'], '22222')
            self.update_qty_on_hand(
                self.product1, self.stock_wh.lot_stock_id, 10)
            self.assertEquals(self.product1.with_context(
                location=self.stock_wh.lot_stock_id.id).qty_available, 10)
            move = self.env['stock.move'].search([], order='id desc')[0]
            self.assertEquals(len(move), 1)
            self.assertEquals(move.product_id, self.product1)
            self.assertEquals(move.product_uom_qty, 10)
            self.force_future_write_date(move)
            fname, content = product_obj.beezup_generate_file(
                'standard', company_id=company_id)
            self.assertEquals(fname, self.fname_us)
            self.assertTrue(os.path.exists(self.fname_us))
            self.assertFalse(os.path.exists(self.fname_us_lock))
            self.assertEquals(len(content), 2)
            for _index, row in content.iterrows():
                if row['id'] == self.product1.id:
                    self.assertEquals(row['name'], 'Test product 1')
                    self.assertEquals(row['barcode'], '8435502834914')
                    self.assertEquals(row['customer_price'], 100)
                    self.assertEquals(row['weight'], 3)
                    self.assertEquals(row['qty_available'], 10)
                    self.assertEquals(row['stock_web'], 10)
                    self.assertEquals(row['default_code'], '20056')
                elif row['id'] == self.product2.id:
                    self.assertEquals(row['name'], 'Test product 2')
                    self.assertEquals(row['barcode'], '7501031311309')
                    self.assertEquals(row['customer_price'], 200)
                    self.assertEquals(row['weight'], 4)
                    self.assertEquals(row['qty_available'], 0)
                    self.assertEquals(row['stock_web'], 0)
                    self.assertEquals(row['default_code'], '22222')
        elif test == 'type_5':
            fname, content = product_obj.beezup_generate_file(
                'standard', company_id=company_id)
            self.assertEquals(fname, self.fname_us)
            self.assertTrue(os.path.exists(self.fname_us))
            self.assertFalse(os.path.exists(self.fname_us_lock))
            self.assertEquals(len(content), 2)
            for _index, row in content.iterrows():
                if row['id'] == self.product1.id:
                    self.assertEquals(row['name'], 'Test product 1')
                    self.assertEquals(row['barcode'], '8435502834914')
                    self.assertEquals(row['customer_price'], 100)
                    self.assertEquals(row['weight'], 3)
                    self.assertEquals(row['qty_available'], 0)
                    self.assertEquals(row['stock_web'], 0)
                    self.assertEquals(row['default_code'], '20056')
                elif row['id'] == self.product2.id:
                    self.assertEquals(row['name'], 'Test product 2')
                    self.assertEquals(row['barcode'], '7501031311309')
                    self.assertEquals(row['customer_price'], 200)
                    self.assertEquals(row['weight'], 4)
                    self.assertEquals(row['qty_available'], 0)
                    self.assertEquals(row['stock_web'], 0)
                    self.assertEquals(row['default_code'], '22222')
            self.update_qty_on_hand(
                self.product1, self.stock_wh.lot_stock_id, 10)
            self.assertEquals(self.product1.with_context(
                location=self.stock_wh.lot_stock_id.id).qty_available, 10)
            move = self.env['stock.move'].search([], order='id desc')[0]
            self.assertEquals(len(move), 1)
            self.assertEquals(move.product_id, self.product1)
            self.assertEquals(move.product_uom_qty, 10)
            self.force_future_write_date(move)
            self.product3.export_to_beezup = True
            self.force_future_write_date(self.product3)
            fname, content = product_obj.beezup_generate_file(
                'standard', company_id=company_id)
            self.assertEquals(fname, self.fname_us)
            self.assertTrue(os.path.exists(self.fname_us))
            self.assertFalse(os.path.exists(self.fname_us_lock))
            self.assertEquals(len(content), 3)
            for _index, row in content.iterrows():
                if row['id'] == self.product1.id:
                    self.assertEquals(row['name'], 'Test product 1')
                    self.assertEquals(row['barcode'], '8435502834914')
                    self.assertEquals(row['customer_price'], 100)
                    self.assertEquals(row['weight'], 3)
                    self.assertEquals(row['qty_available'], 10)
                    self.assertEquals(row['stock_web'], 10)
                    self.assertEquals(row['default_code'], '20056')
                elif row['id'] == self.product2.id:
                    self.assertEquals(row['name'], 'Test product 2')
                    self.assertEquals(row['barcode'], '7501031311309')
                    self.assertEquals(row['customer_price'], 200)
                    self.assertEquals(row['weight'], 4)
                    self.assertEquals(row['qty_available'], 0)
                    self.assertEquals(row['stock_web'], 0)
                    self.assertEquals(row['default_code'], '22222')
                elif row['id'] == self.product3.id:
                    self.assertEquals(row['name'], 'Test product 3')
                    self.assertEquals(row['barcode'], '4317784094610')
                    self.assertEquals(row['customer_price'], 300)
                    self.assertEquals(row['weight'], 5)
                    self.assertEquals(row['qty_available'], 0)
                    self.assertEquals(row['stock_web'], 0)
                    self.assertEquals(row['default_code'], '88888')
        elif test == 'type_6':
            fname, content = product_obj.beezup_generate_file(
                'standard', company_id=company_id)
            self.assertEquals(fname, self.fname_us)
            self.assertTrue(os.path.exists(self.fname_us))
            self.assertFalse(os.path.exists(self.fname_us_lock))
            self.assertEquals(len(content), 3)
            for _index, row in content.iterrows():
                if row['id'] == self.product1.id:
                    self.assertEquals(row['name'], 'Test product 1')
                    self.assertEquals(row['barcode'], '8435502834914')
                    self.assertEquals(row['customer_price'], 100)
                    self.assertEquals(row['weight'], 3)
                    self.assertEquals(row['qty_available'], 0)
                    self.assertEquals(row['stock_web'], 0)
                    self.assertEquals(row['default_code'], '20056')
                elif row['id'] == self.product2.id:
                    self.assertEquals(row['name'], 'Test product 2')
                    self.assertEquals(row['barcode'], '7501031311309')
                    self.assertEquals(row['customer_price'], 200)
                    self.assertEquals(row['weight'], 4)
                    self.assertEquals(row['qty_available'], 0)
                    self.assertEquals(row['stock_web'], 0)
                    self.assertEquals(row['default_code'], '22222')
                elif row['id'] == self.product3.id:
                    self.assertEquals(row['name'], 'Test product 3')
                    self.assertEquals(row['barcode'], '4317784094610')
                    self.assertEquals(row['customer_price'], 300)
                    self.assertEquals(row['weight'], 5)
                    self.assertEquals(row['qty_available'], 0)
                    self.assertEquals(row['stock_web'], 0)
                    self.assertEquals(row['default_code'], '88888')
            self.product1.unlink()
            company = self.env.user.company_id
            self.assertEquals(
                company.beezup_product_ids2delete, '%s' % self.product1.id)
            self.product2.unlink()
            self.assertEquals(
                company.beezup_product_ids2delete, '%s, %s' % (
                    str(self.product1.id), str(self.product2.id)))
            fname, content = product_obj.beezup_generate_file(
                'standard', company_id=company_id)
            self.assertEquals(fname, self.fname_us)
            self.assertTrue(os.path.exists(self.fname_us))
            self.assertFalse(os.path.exists(self.fname_us_lock))
            self.assertEquals(len(content), 1)
            for _index, row in content.iterrows():
                if row['id'] == self.product3.id:
                    self.assertEquals(row['name'], 'Test product 3')
                    self.assertEquals(row['barcode'], '4317784094610')
                    self.assertEquals(row['customer_price'], 300)
                    self.assertEquals(row['weight'], 5)
                    self.assertEquals(row['qty_available'], 0)
                    self.assertEquals(row['stock_web'], 0)
                    self.assertEquals(row['default_code'], '88888')
        elif test == 'type_7':
            fname_es, content = product_obj.beezup_generate_file(
                'standard', lang='es_ES', company_id=company_id)
            self.assertEquals(fname_es, self.fname_es)
            self.assertTrue(os.path.exists(self.fname_es))
            self.assertFalse(os.path.exists(self.fname_es_lock))
            self.assertEquals(len(content), 1)
            for _index, row in content.iterrows():
                self.assertEquals(row['id'], self.product1.id)
                self.assertEquals(row['name'], 'Test product 1')
                self.assertEquals(row['barcode'], '8435502834914')
                self.assertEquals(row['customer_price'], 100)
                self.assertEquals(row['weight'], 3)
                self.assertEquals(row['qty_available'], 0)
                self.assertEquals(row['stock_web'], 0)
                self.assertEquals(row['default_code'], '20056')
            fname_pt, content = product_obj.beezup_generate_file(
                'standard', lang='pt_PT', company_id=company_id)
            self.assertEquals(fname_pt, self.fname_pt)
            self.assertTrue(os.path.exists(self.fname_pt))
            self.assertFalse(os.path.exists(self.fname_pt_lock))
            self.assertEquals(len(content), 1)
            for _index, row in content.iterrows():
                self.assertEquals(row['id'], self.product1.id)
                self.assertEquals(row['name'], 'Test product 1')
                self.assertEquals(row['barcode'], '8435502834914')
                self.assertEquals(row['customer_price'], 100)
                self.assertEquals(row['weight'], 3)
                self.assertEquals(row['qty_available'], 0)
                self.assertEquals(row['stock_web'], 0)
                self.assertEquals(row['default_code'], '20056')
            self.assertTrue(os.path.exists(self.fname_es))
            self.assertFalse(os.path.exists(self.fname_es_lock))
            fname, content = product_obj.beezup_generate_file(
                'standard', company_id=company_id)
            self.assertEquals(fname, self.fname_us)
            self.assertTrue(os.path.exists(self.fname_us))
            self.assertFalse(os.path.exists(self.fname_us_lock))
            self.assertEquals(len(content), 1)
            for _index, row in content.iterrows():
                self.assertEquals(row['id'], self.product1.id)
                self.assertEquals(row['name'], 'Test product 1')
                self.assertEquals(row['barcode'], '8435502834914')
                self.assertEquals(row['customer_price'], 100)
                self.assertEquals(row['weight'], 3)
                self.assertEquals(row['qty_available'], 0)
                self.assertEquals(row['stock_web'], 0)
                self.assertEquals(row['default_code'], '20056')
            self.assertTrue(os.path.exists(self.fname_es))
            self.assertTrue(os.path.exists(self.fname_pt))
            self.assertFalse(os.path.exists(self.fname_es_lock))
            self.assertFalse(os.path.exists(self.fname_pt_lock))
        elif test == 'type_8':
            fname2, content2 = self.product1.beezup_generate_file(
                'update_stock', company_id=company_id)
            self.assertEquals(fname2, self.fname_update_stock_us)
            self.assertTrue(os.path.exists(self.fname_update_stock_us))
            self.assertFalse(os.path.exists(self.fname_update_stock_us_lock))
            self.assertEquals(len(content2), 1)
            for _index, row in content2.iterrows():
                self.assertEquals(row['id'], self.product1.id)
                self.assertEquals(row['name'], 'Test product 1')
                self.assertEquals(row['barcode'], '8435502834914')
                self.assertEquals(row['customer_price'], 100)
                self.assertFalse(row['category'])
                self.assertEquals(row['qty_available'], 10.0)
            content_last = self.product1.beezup_get_file_last('update_stock')
            self.assertEquals(len(content_last), 1)
            for _index, row in content_last.iterrows():
                self.assertEquals(row['id'], self.product1.id)
                self.assertEquals(row['name'], 'Test product 1')
                self.assertEquals(row['barcode'], '8435502834914')
                self.assertEquals(row['customer_price'], 100)
                self.assertFalse(row['category'])
                self.assertEquals(row['qty_available'], 10.0)
        elif test == 'type_9':
            fname, content = product_obj.beezup_generate_file(
                'update_stock', company_id=company_id)
            self.assertEquals(fname, self.fname_update_stock_us)
            self.assertTrue(os.path.exists(self.fname_update_stock_us))
            self.assertFalse(os.path.exists(self.fname_update_stock_us_lock))
            self.assertEquals(len(content), 1)
            for _index, row in content.iterrows():
                self.assertEquals(row['id'], self.product1.id)
                self.assertEquals(row['name'], 'Test product 1')
                self.assertEquals(row['barcode'], '8435502834914')
                self.assertEquals(row['customer_price'], 100)
                self.assertFalse(row['category'])
                self.assertEquals(row['qty_available'], 10)
            self.update_qty_on_hand(
                self.product1, self.stock_wh.lot_stock_id, 50)
            self.assertEquals(self.product1.with_context(
                location=self.stock_wh.lot_stock_id.id).qty_available, 50)
            move2 = self.env['stock.move'].search([], order='id desc')[0]
            self.assertEquals(len(move2), 1)
            self.assertEquals(move2.state, 'done')
            self.assertEquals(move2.product_id, self.product1)
            self.assertEquals(move2.product_uom_qty, 50 - 10)
            self.force_future_write_date(move2)
            fname2, content2 = product_obj.beezup_generate_file(
                'update_stock', company_id=company_id)
            self.assertEquals(fname2, self.fname_update_stock_us)
            self.assertTrue(os.path.exists(self.fname_update_stock_us))
            self.assertFalse(os.path.exists(self.fname_update_stock_us_lock))
            self.assertEquals(len(content2), 1)
            for _index, row in content2.iterrows():
                self.assertEquals(row['id'], self.product1.id)
                self.assertEquals(row['name'], 'Test product 1')
                self.assertEquals(row['barcode'], '8435502834914')
                self.assertEquals(row['customer_price'], 100)
                self.assertFalse(row['category'])
                self.assertEquals(row['qty_available'], 50)
        elif test == 'type_10':
            fname, content = product_obj.beezup_generate_file(
                'update_stock', company_id=company_id)
            self.assertEquals(fname, self.fname_update_stock_us)
            self.assertTrue(os.path.exists(self.fname_update_stock_us))
            self.assertFalse(os.path.exists(self.fname_update_stock_us_lock))
            self.assertEquals(len(content), 1)
            for _index, row in content.iterrows():
                self.assertEquals(row['id'], self.product1.id)
                self.assertEquals(row['name'], 'Test product 1')
                self.assertEquals(row['barcode'], '8435502834914')
                self.assertEquals(row['customer_price'], 100)
                self.assertFalse(row['category'])
                self.assertEquals(row['qty_available'], 10.0)
            self.update_qty_on_hand(
                self.product2, self.stock_wh.lot_stock_id, 100)
            self.assertEquals(self.product2.with_context(
                location=self.stock_wh.lot_stock_id.id).qty_available, 100)
            move = self.env['stock.move'].search([], order='id desc')[0]
            self.assertEquals(len(move), 1)
            self.assertEquals(move.state, 'done')
            self.assertEquals(move.product_id, self.product2)
            self.assertEquals(move.product_uom_qty, 100)
            self.force_future_write_date(move)
            fname, content = product_obj.beezup_generate_file(
                'update_stock', company_id=company_id)
            self.assertEquals(fname, self.fname_update_stock_us)
            self.assertTrue(os.path.exists(self.fname_update_stock_us))
            self.assertFalse(os.path.exists(self.fname_update_stock_us_lock))
            self.assertEquals(len(content), 2)
            for _index, row in content.iterrows():
                if row['id'] == self.product1.id:
                    self.assertEquals(row['name'], 'Test product 1')
                    self.assertEquals(row['barcode'], '8435502834914')
                    self.assertEquals(row['customer_price'], 100)
                    self.assertFalse(row['category'])
                    self.assertEquals(row['qty_available'], 10.0)
                if row['id'] == self.product2.id:
                    self.assertEquals(row['name'], 'Test product 2')
                    self.assertEquals(row['barcode'], '7501031311309')
                    self.assertEquals(row['customer_price'], 200)
                    self.assertFalse(row['category'])
                    self.assertEquals(row['qty_available'], 100.0)
        elif test == 'type_11':
            fname, content = product_obj.beezup_generate_file(
                'update_stock', company_id=company_id)
            self.assertEquals(fname, self.fname_update_stock_us)
            self.assertTrue(os.path.exists(self.fname_update_stock_us))
            self.assertFalse(os.path.exists(self.fname_update_stock_us_lock))
            self.assertEquals(len(content), 2)
            for _index, row in content.iterrows():
                if row['id'] == self.product2.id:
                    self.assertEquals(row['name'], 'Test product 2')
                    self.assertEquals(row['barcode'], '7501031311309')
                    self.assertEquals(row['customer_price'], 200)
                    self.assertFalse(row['category'])
                    self.assertEquals(row['qty_available'], 100.0)
                if row['id'] == self.product3.id:
                    self.assertEquals(row['name'], 'Test product 3')
                    self.assertEquals(row['barcode'], '4317784094610')
                    self.assertEquals(row['customer_price'], 300)
                    self.assertFalse(row['category'])
                    self.assertEquals(row['qty_available'], 88.0)
            self.product1.unlink()
            company = self.env.user.company_id
            self.assertEquals(
                company.beezup_product_ids2delete, '%s' % self.product1.id)
            self.update_qty_on_hand(
                self.product3, self.stock_wh.lot_stock_id, 99)
            self.assertEquals(self.product3.with_context(
                location=self.stock_wh.lot_stock_id.id).qty_available, 99)
            move = self.env['stock.move'].search([], order='id desc')[0]
            self.assertEquals(len(move), 1)
            self.assertEquals(move.state, 'done')
            self.assertEquals(move.product_id, self.product3)
            self.assertEquals(move.product_uom_qty, 99 - 88)
            self.force_future_write_date(move)
            fname, content = product_obj.beezup_generate_file(
                'update_stock', company_id=company_id)
            self.assertEquals(fname, self.fname_update_stock_us)
            self.assertTrue(os.path.exists(self.fname_update_stock_us))
            self.assertFalse(os.path.exists(self.fname_update_stock_us_lock))
            self.assertEquals(len(content), 2)
            for _index, row in content.iterrows():
                if row['id'] == self.product2.id:
                    self.assertEquals(row['name'], 'Test product 2')
                    self.assertEquals(row['barcode'], '7501031311309')
                    self.assertEquals(row['customer_price'], 200)
                    self.assertFalse(row['category'])
                    self.assertEquals(row['qty_available'], 100.0)
                if row['id'] == self.product3.id:
                    self.assertEquals(row['name'], 'Test product 3')
                    self.assertEquals(row['barcode'], '4317784094610')
                    self.assertEquals(row['customer_price'], 300)
                    self.assertFalse(row['category'])
                    self.assertEquals(row['qty_available'], 99.0)
        elif test == 'type_12':
            fname_update_stock_pt, content = (
                product_obj.beezup_generate_file(
                    'update_stock', lang='pt_PT', company_id=company_id))
            self.assertEquals(
                fname_update_stock_pt, self.fname_update_stock_pt)
            self.assertTrue(os.path.exists(self.fname_update_stock_pt))
            self.assertFalse(os.path.exists(self.fname_update_stock_pt_lock))
            self.assertEquals(len(content), 1)
            for _index, row in content.iterrows():
                self.assertEquals(row['id'], self.product1.id)
                self.assertEquals(row['name'], 'Test product 1')
                self.assertEquals(row['barcode'], '8435502834914')
                self.assertEquals(row['customer_price'], 100)
                self.assertFalse(row['category'])
                self.assertEquals(row['qty_available'], 50.0)
            self.assertTrue(os.path.exists(self.fname_update_stock_es))
            self.assertFalse(os.path.exists(self.fname_update_stock_es_lock))
            self.update_qty_on_hand(
                self.product1, self.stock_wh.lot_stock_id, 75)
            self.assertEquals(self.product1.with_context(
                location=self.stock_wh.lot_stock_id.id).qty_available, 75)
            move = self.env['stock.move'].search([], order='id desc')[0]
            self.assertEquals(len(move), 1)
            self.assertEquals(move.state, 'done')
            self.assertEquals(move.product_id, self.product1)
            self.assertEquals(move.product_uom_qty, 75 - 50)
            self.force_future_write_date(move)
            fname_update_stock_us, content = (
                product_obj.beezup_generate_file(
                    'update_stock', company_id=company_id))
            self.assertEquals(
                fname_update_stock_us, self.fname_update_stock_us)
            self.assertTrue(os.path.exists(self.fname_update_stock_us))
            self.assertFalse(os.path.exists(self.fname_update_stock_us_lock))
            self.assertEquals(len(content), 1)
            for _index, row in content.iterrows():
                self.assertEquals(row['id'], self.product1.id)
                self.assertEquals(row['name'], 'Test product 1')
                self.assertEquals(row['barcode'], '8435502834914')
                self.assertEquals(row['customer_price'], 100)
                self.assertFalse(row['category'])
                self.assertEquals(row['qty_available'], 75.0)
            self.assertTrue(os.path.exists(self.fname_update_stock_es))
            self.assertTrue(os.path.exists(self.fname_update_stock_pt))
            self.assertFalse(os.path.exists(self.fname_update_stock_es_lock))
            self.assertFalse(os.path.exists(self.fname_update_stock_pt_lock))
        else:
            raise UserError(_('Review, test key not found!'))

    def test_beezup_csv_file_get_one_product_standard_no_company(self):
        df_file = self.product1.beezup_csv_file_get('standard')
        self.assertEquals(len(df_file), 1)
        for _index, row in df_file.iterrows():
            self.assertEquals(row['id'], self.product1.id)
            self.assertEquals(row['name'], 'Test product 1')
            self.assertEquals(row['barcode'], '8435502834914')
            self.assertEquals(row['customer_price'], 100)
            self.assertEquals(row['weight'], 3)
            self.assertEquals(row['qty_available'], 0)
            self.assertEquals(row['stock_web'], 0)
            self.assertEquals(row['default_code'], '20056')

    def test_beezup_csv_file_get_one_product_standard_company(self):
        df_file = self.product1.beezup_csv_file_get(
            'standard', self.env.user.company_id.id)
        self.assertEquals(len(df_file), 1)
        for _index, row in df_file.iterrows():
            self.assertEquals(row['id'], self.product1.id)
            self.assertEquals(row['name'], 'Test product 1')
            self.assertEquals(row['barcode'], '8435502834914')
            self.assertEquals(row['customer_price'], 100)
            self.assertEquals(row['weight'], 3)
            self.assertEquals(row['qty_available'], 0)
            self.assertEquals(row['stock_web'], 0)
            self.assertEquals(row['default_code'], '20056')

    def test_beezup_csv_file_get_two_products_standard_no_company(self):
        products = self.product1 + self.product2
        df_file = products.beezup_csv_file_get('standard')
        self.assertEquals(len(df_file), 2)
        for _index, row in df_file.iterrows():
            if row['id'] == self.product1.id:
                self.assertEquals(row['name'], 'Test product 1')
                self.assertEquals(row['barcode'], '8435502834914')
                self.assertEquals(row['customer_price'], 100)
                self.assertEquals(row['weight'], 3)
                self.assertEquals(row['qty_available'], 0)
                self.assertEquals(row['stock_web'], 0)
                self.assertEquals(row['default_code'], '20056')
            elif row['id'] == self.product2.id:
                self.assertEquals(row['name'], 'Test product 2')
                self.assertEquals(row['barcode'], '7501031311309')
                self.assertEquals(row['customer_price'], 200)
                self.assertEquals(row['weight'], 4)
                self.assertEquals(row['qty_available'], 0)
                self.assertEquals(row['stock_web'], 0)
                self.assertEquals(row['default_code'], '22222')

    def test_beezup_csv_file_get_two_products_standard_company(self):
        products = self.product1 + self.product2
        df_file = products.beezup_csv_file_get(
            'standard', self.env.user.company_id.id)
        self.assertEquals(len(df_file), 2)
        for _index, row in df_file.iterrows():
            if row['id'] == self.product1.id:
                self.assertEquals(row['name'], 'Test product 1')
                self.assertEquals(row['barcode'], '8435502834914')
                self.assertEquals(row['customer_price'], 100)
                self.assertEquals(row['weight'], 3)
                self.assertEquals(row['qty_available'], 0)
                self.assertEquals(row['stock_web'], 0)
                self.assertEquals(row['default_code'], '20056')
            elif row['id'] == self.product2.id:
                self.assertEquals(row['name'], 'Test product 2')
                self.assertEquals(row['barcode'], '7501031311309')
                self.assertEquals(row['customer_price'], 200)
                self.assertEquals(row['weight'], 4)
                self.assertEquals(row['qty_available'], 0)
                self.assertEquals(row['stock_web'], 0)
                self.assertEquals(row['default_code'], '22222')

    def test_get_file_last_no_params_standard_no_company(self):
        self.remove_files([self.fname_us, self.fname_us_lock])
        self.product2.export_to_beezup = False
        self.product3.export_to_beezup = False
        content = self.product1.beezup_get_file_last('standard')
        self.assertFalse(content)
        self.check_beezup_generate_company('type_1')

    def test_get_file_last_no_params_standard_company(self):
        self.remove_files([self.fname_us, self.fname_us_lock])
        self.product2.export_to_beezup = False
        self.product3.export_to_beezup = False
        content = self.product1.beezup_get_file_last('standard')
        self.assertFalse(content)
        self.check_beezup_generate_company(
            'type_1', self.env.user.company_id.id)

    def test_beezup_generate_file_one_product_again_standard_no_company(self):
        self.remove_files([self.fname_us, self.fname_us_lock])
        self.product2.export_to_beezup = False
        self.product3.export_to_beezup = False
        self.check_beezup_generate_company('type_2')

    def test_beezup_generate_file_one_product_again_standard_company(self):
        self.remove_files([self.fname_us, self.fname_us_lock])
        self.product2.export_to_beezup = False
        self.product3.export_to_beezup = False
        self.check_beezup_generate_company(
            'type_2', self.env.user.company_id.id)

    def test_beezup_generate_file_update_and_new_standard_no_company(self):
        self.remove_files([self.fname_us, self.fname_us_lock])
        self.product3.export_to_beezup = False
        self.check_beezup_generate_company('type_3')

    def test_beezup_generate_file_update_and_new_standard_company(self):
        self.remove_files([self.fname_us, self.fname_us_lock])
        self.product3.export_to_beezup = False
        self.check_beezup_generate_company(
            'type_3', self.env.user.company_id.id)

    def test_beezup_generate_file_update_stock_standard_no_company(self):
        self.remove_files([self.fname_us, self.fname_us_lock])
        self.product3.export_to_beezup = False
        self.check_beezup_generate_company('type_4')

    def test_beezup_generate_file_update_stock_standard_company(self):
        self.remove_files([self.fname_us, self.fname_us_lock])
        self.product3.export_to_beezup = False
        self.check_beezup_generate_company(
            'type_4', self.env.user.company_id.id)

    def test_beezup_generate_file_update_stock_new_standard_no_company(self):
        self.remove_files([self.fname_us, self.fname_us_lock])
        self.product3.export_to_beezup = False
        self.check_beezup_generate_company('type_5')

    def test_beezup_generate_file_update_stock_new_standard_company(self):
        self.remove_files([self.fname_us, self.fname_us_lock])
        self.product3.export_to_beezup = False
        self.check_beezup_generate_company(
            'type_5', self.env.user.company_id.id)

    def test_beezup_generate_file_update_and_drop_standard_no_company(self):
        self.remove_files([self.fname_us, self.fname_us_lock])
        self.check_beezup_generate_company('type_6')

    def test_beezup_generate_file_update_and_drop_standard_company(self):
        self.remove_files([self.fname_us, self.fname_us_lock])
        self.check_beezup_generate_company(
            'type_6', self.env.user.company_id.id)

    def test_beezup_generate_file_params_several_langs_standard_no_company(
            self):
        self.remove_files([
            self.fname_es, self.fname_es_lock,
            self.fname_pt, self.fname_pt_lock,
            self.fname_us, self.fname_us_lock,
        ])
        self.product2.export_to_beezup = False
        self.product3.export_to_beezup = False
        self.check_beezup_generate_company('type_7')

    def test_beezup_generate_file_params_several_langs_standard_company(self):
        self.remove_files([
            self.fname_es, self.fname_es_lock,
            self.fname_pt, self.fname_pt_lock,
            self.fname_us, self.fname_us_lock,
        ])
        self.product2.export_to_beezup = False
        self.product3.export_to_beezup = False
        self.check_beezup_generate_company(
            'type_7', self.env.user.company_id.id)

    def test_beezup_csv_file_get_one_product_update_stock_no_company(self):
        df_file = self.product1.beezup_csv_file_get('update_stock')
        self.assertEquals(len(df_file), 1)
        for _index, row in df_file.iterrows():
            self.assertEquals(row['id'], self.product1.id)
            self.assertEquals(row['name'], 'Test product 1')
            self.assertEquals(row['barcode'], '8435502834914')
            self.assertEquals(row['customer_price'], 100)
            self.assertFalse(row['category'])
            self.assertEquals(row['qty_available'], 0)

    def test_beezup_csv_file_get_one_product_update_stock_company(self):
        df_file = self.product1.beezup_csv_file_get(
            'update_stock', self.env.user.company_id.id)
        self.assertEquals(len(df_file), 1)
        for _index, row in df_file.iterrows():
            self.assertEquals(row['id'], self.product1.id)
            self.assertEquals(row['name'], 'Test product 1')
            self.assertEquals(row['barcode'], '8435502834914')
            self.assertEquals(row['customer_price'], 100)
            self.assertFalse(row['category'])
            self.assertEquals(row['qty_available'], 0)

    def test_beezup_csv_file_get_two_products_update_stock_no_company(self):
        products = self.product1 + self.product2
        df_file = products.beezup_csv_file_get('update_stock')
        self.assertEquals(len(df_file), 2)
        for _index, row in df_file.iterrows():
            if row['id'] == self.product1.id:
                self.assertEquals(row['name'], 'Test product 1')
                self.assertEquals(row['barcode'], '8435502834914')
                self.assertEquals(row['customer_price'], 100)
                self.assertFalse(row['category'])
                self.assertEquals(row['qty_available'], 0)
            elif row['id'] == self.product2.id:
                self.assertEquals(row['name'], 'Test product 2')
                self.assertEquals(row['barcode'], '7501031311309')
                self.assertEquals(row['customer_price'], 200)
                self.assertFalse(row['category'])
                self.assertEquals(row['qty_available'], 0)

    def test_beezup_csv_file_get_two_products_update_stock_company(self):
        products = self.product1 + self.product2
        df_file = products.beezup_csv_file_get(
            'update_stock', self.env.user.company_id.id)
        self.assertEquals(len(df_file), 2)
        for _index, row in df_file.iterrows():
            if row['id'] == self.product1.id:
                self.assertEquals(row['name'], 'Test product 1')
                self.assertEquals(row['barcode'], '8435502834914')
                self.assertEquals(row['customer_price'], 100)
                self.assertFalse(row['category'])
                self.assertEquals(row['qty_available'], 0)
            elif row['id'] == self.product2.id:
                self.assertEquals(row['name'], 'Test product 2')
                self.assertEquals(row['barcode'], '7501031311309')
                self.assertEquals(row['customer_price'], 200)
                self.assertFalse(row['category'])
                self.assertEquals(row['qty_available'], 0)

    def test_get_file_last_no_params_update_stock_no_company(self):
        self.remove_files([
            self.fname_update_stock_us, self.fname_update_stock_us_lock])
        self.product2.export_to_beezup = False
        self.product3.export_to_beezup = False
        content = self.product1.beezup_get_file_last('update_stock')
        self.assertFalse(content)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        self.assertEquals(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        move = self.env['stock.move'].search([], order='id desc')[0]
        self.assertEquals(len(move), 1)
        self.assertEquals(move.state, 'done')
        self.assertEquals(move.product_id, self.product1)
        self.assertEquals(move.product_uom_qty, 10)
        self.force_future_write_date(move)
        self.check_beezup_generate_company('type_8')

    def test_get_file_last_no_params_update_stock_company(self):
        self.remove_files([
            self.fname_update_stock_us, self.fname_update_stock_us_lock])
        self.product2.export_to_beezup = False
        self.product3.export_to_beezup = False
        content = self.product1.beezup_get_file_last('update_stock')
        self.assertFalse(content)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        self.assertEquals(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        move = self.env['stock.move'].search([], order='id desc')[0]
        self.assertEquals(len(move), 1)
        self.assertEquals(move.state, 'done')
        self.assertEquals(move.product_id, self.product1)
        self.assertEquals(move.product_uom_qty, 10)
        self.force_future_write_date(move)
        self.check_beezup_generate_company(
            'type_8', self.env.user.company_id.id)

    def test_beezup_generate_file_one_product_again_update_stock_no_company(
            self):
        self.remove_files([
            self.fname_update_stock_us, self.fname_update_stock_us_lock])
        self.product2.export_to_beezup = False
        self.product3.export_to_beezup = False
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        self.assertEquals(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        move = self.env['stock.move'].search([], order='id desc')[0]
        self.assertEquals(len(move), 1)
        self.assertEquals(move.state, 'done')
        self.assertEquals(move.product_id, self.product1)
        self.assertEquals(move.product_uom_qty, 10)
        self.force_future_write_date(move)
        self.check_beezup_generate_company('type_9')

    def test_beezup_generate_file_one_product_again_update_stock_company(self):
        self.remove_files([
            self.fname_update_stock_us, self.fname_update_stock_us_lock])
        self.product2.export_to_beezup = False
        self.product3.export_to_beezup = False
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        self.assertEquals(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        move = self.env['stock.move'].search([], order='id desc')[0]
        self.assertEquals(len(move), 1)
        self.assertEquals(move.state, 'done')
        self.assertEquals(move.product_id, self.product1)
        self.assertEquals(move.product_uom_qty, 10)
        self.force_future_write_date(move)
        self.check_beezup_generate_company(
            'type_9', self.env.user.company_id.id)

    def test_beezup_generate_file_update_and_new_update_stock_no_company(self):
        self.remove_files([
            self.fname_update_stock_us, self.fname_update_stock_us_lock])
        self.product3.export_to_beezup = False
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        self.assertEquals(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        move = self.env['stock.move'].search([], order='id desc')[0]
        self.assertEquals(len(move), 1)
        self.assertEquals(move.state, 'done')
        self.assertEquals(move.product_id, self.product1)
        self.assertEquals(move.product_uom_qty, 10)
        self.force_future_write_date(move)
        self.check_beezup_generate_company('type_10')

    def test_beezup_generate_file_update_and_new_update_stock_company(self):
        self.remove_files([
            self.fname_update_stock_us, self.fname_update_stock_us_lock])
        self.product3.export_to_beezup = False
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        self.assertEquals(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        move = self.env['stock.move'].search([], order='id desc')[0]
        self.assertEquals(len(move), 1)
        self.assertEquals(move.state, 'done')
        self.assertEquals(move.product_id, self.product1)
        self.assertEquals(move.product_uom_qty, 10)
        self.force_future_write_date(move)
        self.check_beezup_generate_company(
            'type_10', self.env.user.company_id.id)

    def test_beezup_generate_file_update_and_drop_update_stock_no_company(
            self):
        self.remove_files([
            self.fname_update_stock_us, self.fname_update_stock_us_lock])
        self.update_qty_on_hand(self.product2, self.stock_wh.lot_stock_id, 100)
        self.assertEquals(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        move = self.env['stock.move'].search([], order='id desc')[0]
        self.assertEquals(len(move), 1)
        self.assertEquals(move.state, 'done')
        self.assertEquals(move.product_id, self.product2)
        self.assertEquals(move.product_uom_qty, 100)
        self.force_future_write_date(move)
        self.update_qty_on_hand(self.product3, self.stock_wh.lot_stock_id, 88)
        self.assertEquals(self.product3.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 88)
        move = self.env['stock.move'].search([], order='id desc')[0]
        self.assertEquals(len(move), 1)
        self.assertEquals(move.state, 'done')
        self.assertEquals(move.product_id, self.product3)
        self.assertEquals(move.product_uom_qty, 88)
        self.force_future_write_date(move)
        self.check_beezup_generate_company('type_11')

    def test_beezup_generate_file_update_and_drop_update_stock_company(self):
        self.remove_files([
            self.fname_update_stock_us, self.fname_update_stock_us_lock])
        self.update_qty_on_hand(self.product2, self.stock_wh.lot_stock_id, 100)
        self.assertEquals(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        move = self.env['stock.move'].search([], order='id desc')[0]
        self.assertEquals(len(move), 1)
        self.assertEquals(move.state, 'done')
        self.assertEquals(move.product_id, self.product2)
        self.assertEquals(move.product_uom_qty, 100)
        self.force_future_write_date(move)
        self.update_qty_on_hand(self.product3, self.stock_wh.lot_stock_id, 88)
        self.assertEquals(self.product3.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 88)
        move = self.env['stock.move'].search([], order='id desc')[0]
        self.assertEquals(len(move), 1)
        self.assertEquals(move.state, 'done')
        self.assertEquals(move.product_id, self.product3)
        self.assertEquals(move.product_uom_qty, 88)
        self.force_future_write_date(move)
        self.check_beezup_generate_company(
            'type_11', self.env.user.company_id.id)

    def test_beezup_generate_file_params_several_langs_update_stock_no_company(
            self):
        self.remove_files([
            self.fname_update_stock_es, self.fname_update_stock_es_lock,
            self.fname_update_stock_pt, self.fname_update_stock_pt_lock,
            self.fname_update_stock_us, self.fname_update_stock_us_lock
        ])
        self.product2.export_to_beezup = False
        self.product3.export_to_beezup = False
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        self.assertEquals(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        move = self.env['stock.move'].search([], order='id desc')[0]
        self.assertEquals(len(move), 1)
        self.assertEquals(move.state, 'done')
        self.assertEquals(move.product_id, self.product1)
        self.assertEquals(move.product_uom_qty, 10)
        self.force_future_write_date(move)
        fname_update_stock_es, content = (
            self.env['product.product'].beezup_generate_file(
                'update_stock', lang='es_ES'))
        self.assertEquals(fname_update_stock_es, self.fname_update_stock_es)
        self.assertTrue(os.path.exists(self.fname_update_stock_es))
        self.assertFalse(os.path.exists(self.fname_update_stock_es_lock))
        self.assertEquals(len(content), 1)
        for _index, row in content.iterrows():
            self.assertEquals(row['id'], self.product1.id)
            self.assertEquals(row['name'], 'Test product 1')
            self.assertEquals(row['barcode'], '8435502834914')
            self.assertEquals(row['customer_price'], 100)
            self.assertFalse(row['category'])
            self.assertEquals(row['qty_available'], 10)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 50)
        self.assertEquals(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 50)
        move = self.env['stock.move'].search([], order='id desc')[0]
        self.assertEquals(len(move), 1)
        self.assertEquals(move.state, 'done')
        self.assertEquals(move.product_id, self.product1)
        self.assertEquals(move.product_uom_qty, 50 - 10)
        self.force_future_write_date(move)
        self.check_beezup_generate_company('type_12')

    def test_beezup_generate_file_params_several_langs_update_stock_company(
            self):
        self.remove_files([
            self.fname_update_stock_es, self.fname_update_stock_es_lock,
            self.fname_update_stock_pt, self.fname_update_stock_pt_lock,
            self.fname_update_stock_us, self.fname_update_stock_us_lock
        ])
        self.product2.export_to_beezup = False
        self.product3.export_to_beezup = False
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        self.assertEquals(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        move = self.env['stock.move'].search([], order='id desc')[0]
        self.assertEquals(len(move), 1)
        self.assertEquals(move.state, 'done')
        self.assertEquals(move.product_id, self.product1)
        self.assertEquals(move.product_uom_qty, 10)
        self.force_future_write_date(move)
        fname_update_stock_es, content = (
            self.env['product.product'].beezup_generate_file(
                'update_stock', lang='es_ES'))
        self.assertEquals(fname_update_stock_es, self.fname_update_stock_es)
        self.assertTrue(os.path.exists(self.fname_update_stock_es))
        self.assertFalse(os.path.exists(self.fname_update_stock_es_lock))
        self.assertEquals(len(content), 1)
        for _index, row in content.iterrows():
            self.assertEquals(row['id'], self.product1.id)
            self.assertEquals(row['name'], 'Test product 1')
            self.assertEquals(row['barcode'], '8435502834914')
            self.assertEquals(row['customer_price'], 100)
            self.assertFalse(row['category'])
            self.assertEquals(row['qty_available'], 10)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 50)
        self.assertEquals(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 50)
        move = self.env['stock.move'].search([], order='id desc')[0]
        self.assertEquals(len(move), 1)
        self.assertEquals(move.state, 'done')
        self.assertEquals(move.product_id, self.product1)
        self.assertEquals(move.product_uom_qty, 50 - 10)
        self.force_future_write_date(move)
        self.check_beezup_generate_company(
            'type_12', self.env.user.company_id.id)

    def test_beezup_image_get_one_image(self):
        url = 'https://trey.es/web/image/website/1/logo?unique=20ee16c'
        images, warns = self.images_get(url)
        self.assertTrue(images)
        self.assertFalse(warns)
        image = images and images[0] or None
        self.product1.product_tmpl_id.write({
            'image': image,
            'product_image_ids': [
                (0, 0, {'image': i}) for i in images
            ],
        })
        self.assertTrue(self.product1.product_tmpl_id.image)
        self.assertTrue(self.product1.product_tmpl_id.product_image_ids)
        res = self.product1.image_get(self.product1.id)
        self.assertTrue(res)
        self.remove_files([self.fname_us, self.fname_us_lock])
        df_file = self.product1.beezup_csv_file_get('standard')
        self.assertEquals(len(df_file), 1)
        for _index, row in df_file.iterrows():
            self.assertEquals(row['id'], self.product1.id)
            self.assertEquals(row['name'], 'Test product 1')
            self.assertEquals(row['barcode'], '8435502834914')
            self.assertEquals(row['customer_price'], 100)
            self.assertFalse(row['category'])
            self.assertEquals(row['qty_available'], 0)
            self.assertIn('beezup/image', row['image_0'])
            self.assertIn('beezup/image', row['image_1'])

    def test_beezup_image_get_without_image(self):
        self.product1.product_tmpl_id.write({
            'image': None,
            'product_image_ids': [(6, 0, [])],
        })
        self.assertFalse(self.product1.product_tmpl_id.image)
        self.assertFalse(self.product1.product_tmpl_id.product_image_ids)
        image = self.product1.image_get(self.product1.id, 0)
        self.assertFalse(image)
        with self.assertRaises(Exception):
            self.product1.image_get(self.product1.id, 2)

    def test_beezup_image_get_url_not_exists(self):
        url = 'https://url_invent/image_no_exist'
        images, warns = self.images_get(url)
        self.assertFalse(images)
        self.assertTrue(warns)
        image = self.product1.image_get(self.product1.id, 0)
        self.assertFalse(image)
        with self.assertRaises(Exception):
            self.product1.image_get(self.product1.id, 2)

    def test_beezup_web_categories(self):
        public_categ1 = self.env['product.public.category'].create({
            'name': 'Test category 1',
        })
        self.product1.public_categ_ids = [(6, 0, public_categ1.ids)]
        df_file = self.product1.beezup_csv_file_get('update_stock')
        self.assertEquals(len(df_file), 1)
        for _index, row in df_file.iterrows():
            self.assertEquals(row['id'], self.product1.id)
            self.assertEquals(row['name'], 'Test product 1')
            self.assertEquals(row['barcode'], '8435502834914')
            self.assertEquals(row['customer_price'], 100)
            self.assertEquals(row['category'], 'Test category 1')
            self.assertEquals(row['qty_available'], 0)
        public_categ2 = self.env['product.public.category'].create({
            'name': 'Test category 2',
        })
        self.product1.public_categ_ids = [(4, public_categ2.id)]
        df_file = self.product1.beezup_csv_file_get('update_stock')
        self.assertEquals(len(df_file), 1)
        for _index, row in df_file.iterrows():
            self.assertEquals(row['id'], self.product1.id)
            self.assertEquals(row['name'], 'Test product 1')
            self.assertEquals(row['barcode'], '8435502834914')
            self.assertEquals(row['customer_price'], 100)
            self.assertEquals(
                row['category'], 'Test category 1, Test category 2')
            self.assertEquals(row['qty_available'], 0)
