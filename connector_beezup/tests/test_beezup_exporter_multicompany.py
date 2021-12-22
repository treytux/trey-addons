###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging
import os
from datetime import timedelta

from odoo import fields, tools
from odoo.tests.common import TransactionCase

_log = logging.getLogger(__name__)


class TestBeezupExporterMulticompany(TransactionCase):

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
        self.company1 = self.env.ref('base.main_company')
        self.company2 = self.env['res.company'].create({
            'name': 'New test company'
        })
        self.public_pricelist_company1 = self.env.ref('product.list0')
        self.public_pricelist_company2 = self.public_pricelist_company1.copy({
            'company_id': self.company2.id,
        })
        self.company1.beezup_pricelist_id = self.public_pricelist_company1.id
        self.company2.beezup_pricelist_id = self.public_pricelist_company2.id
        self.product1 = self.env['product.product'].create({
            'company_id': self.company1.id,
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
            'company_id': self.company2.id,
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
            'company_id': None,
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

    def test_beezup_multicompany_no_company(self):
        self.remove_files([self.fname_us, self.fname_us_lock])
        self.product2.export_to_beezup = False
        self.product3.export_to_beezup = False
        fname, content = self.env['product.product'].beezup_generate_file(
            'standard')
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
        self.product2.export_to_beezup = True
        fname, content = self.env['product.product'].beezup_generate_file(
            'standard')
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

    def test_beezup_multicompany_company1(self):
        self.remove_files([self.fname_us, self.fname_us_lock])
        self.product2.export_to_beezup = False
        self.product3.export_to_beezup = False
        fname, content = self.env['product.product'].beezup_generate_file(
            'standard', company_id=self.company1.id)
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
        self.product2.export_to_beezup = True
        fname, content = self.env['product.product'].beezup_generate_file(
            'standard', company_id=self.company1.id)
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

    def test_beezup_multicompany_company2(self):
        self.remove_files([self.fname_us, self.fname_us_lock])
        self.product2.export_to_beezup = False
        self.product3.export_to_beezup = False
        fname, content = self.env['product.product'].beezup_generate_file(
            'standard', company_id=self.company2.id)
        self.assertEquals(fname, self.fname_us)
        self.assertTrue(os.path.exists(self.fname_us))
        self.assertFalse(os.path.exists(self.fname_us_lock))
        self.assertEquals(len(content), 0)
        self.product2.export_to_beezup = True
        self.force_future_write_date(self.product2)
        fname, content = self.env['product.product'].beezup_generate_file(
            'standard', company_id=self.company2.id)
        self.assertEquals(fname, self.fname_us)
        self.assertTrue(os.path.exists(self.fname_us))
        self.assertFalse(os.path.exists(self.fname_us_lock))
        self.assertEquals(len(content), 1)
        for _index, row in content.iterrows():
            self.assertEquals(row['id'], self.product2.id)
            self.assertEquals(row['name'], 'Test product 2')
            self.assertEquals(row['barcode'], '7501031311309')
            self.assertEquals(row['customer_price'], 200)
            self.assertEquals(row['weight'], 4)
            self.assertEquals(row['qty_available'], 0)
            self.assertEquals(row['stock_web'], 0)
            self.assertEquals(row['default_code'], '22222')
