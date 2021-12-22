###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging
import os

from odoo import tools
from odoo.tests.common import TransactionCase

_log = logging.getLogger(__name__)

try:
    import pandas as pd
except (ImportError, IOError) as err:
    _log.debug(err)


class TestBeezupBaseException(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.user.company_id
        self.user_demo = self.env.ref('base.user_demo')
        self.product_model = self.env['ir.model'].search([
            ('model', '=', 'product.product')
        ])
        self.assertEquals(len(self.product_model), 1)
        self.activity_type_warn_id = (
            self.ref('mail.mail_activity_data_warning'))
        (self.fname_us,
         self.fname_us_lock,
         self.fname_update_stock_us,
         self.fname_update_stock_us_lock) = self.generate_lang_files('en_US')
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
            'list_price': 100,
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

    def generate_empty_file(self, fname):
        df = pd.DataFrame(columns=[])
        fname = os.path.join(
            tools.config.filestore(self.env.cr.dbname), fname)
        df.to_csv(fname, header=True, index=False, sep=';')

    def create_base_exception(
            self, function_name, function_params, action_to_launch,
            company_id=None):
        return self.env['base.manage.exception'].create({
            'name': 'Beezup exception tracking',
            'line_ids': [
                (0, 0, {
                    'name': 'Exception line 1',
                    'company_id': company_id,
                    'user_ids': [(6, 0, self.user_demo.ids)],
                    'model_id': self.product_model.id,
                    'function_name': function_name,
                    'function_params': function_params,
                    'action_to_launch': action_to_launch,
                }),
            ]
        })

    def test_beezup_get_file_last_exception_file_type_unknown_no_company(self):
        params = {
            'file_type': 'new_type',
        }
        base_exception = self.create_base_exception(
            'beezup_get_file_last', params, 'schedule_activity_exception',
            self.company.id)
        base_exception.line_ids.run()
        mail_activities = self.env['mail.activity'].search([
            ('activity_type_id', '=', self.activity_type_warn_id),
            ('res_id', '=', base_exception.line_ids[0].id),
            ('user_id', '=', self.user_demo.id),
            ('summary', '=', 'File type unknown!'),
        ])
        self.assertEquals(len(mail_activities), 1)
        self.generate_empty_file('beezup_en_US.lock')
        params = {
            'file_type': 'standard',
        }
        base_exception = self.create_base_exception(
            'beezup_generate_file', params, 'schedule_activity_exception',
            self.company.id)
        base_exception.line_ids.run()
        mail_activities = self.env['mail.activity'].search([
            ('activity_type_id', '=', self.activity_type_warn_id),
            ('res_id', '=', base_exception.line_ids[0].id),
            ('user_id', '=', self.user_demo.id),
            ('summary', '=', 'Process generatte file running...'),
        ])
        self.assertEquals(len(mail_activities), 1)

    def test_beezup_get_file_last_exception_file_type_unknown_company(self):
        params = {
            'file_type': 'new_type',
        }
        base_exception = self.create_base_exception(
            'beezup_get_file_last', params, 'schedule_activity_exception',
            self.company.id)
        base_exception.line_ids.run()
        mail_activities = self.env['mail.activity'].search([
            ('activity_type_id', '=', self.activity_type_warn_id),
            ('res_id', '=', base_exception.line_ids[0].id),
            ('user_id', '=', self.user_demo.id),
            ('summary', '=', 'File type unknown!'),
        ])
        self.assertEquals(len(mail_activities), 1)
        self.generate_empty_file('beezup_en_US.lock')
        params = {
            'file_type': 'standard',
            'company_id': self.company.id,
        }
        base_exception = self.create_base_exception(
            'beezup_generate_file',
            params,
            'schedule_activity_exception', self.company.id)
        base_exception.line_ids.run()
        mail_activities = self.env['mail.activity'].search([
            ('activity_type_id', '=', self.activity_type_warn_id),
            ('res_id', '=', base_exception.line_ids[0].id),
            ('user_id', '=', self.user_demo.id),
            ('summary', '=', 'Process generatte file running...'),
        ])
        self.assertEquals(len(mail_activities), 1)

    def test_beezup_several_params(self):
        params = {
            'file_type': 'new_type',
            'lang': 'es_ES',
        }
        base_exception = self.create_base_exception(
            'beezup_get_file_last', params, 'schedule_activity_exception',
            self.company.id)
        base_exception.line_ids.run()
        mail_activities = self.env['mail.activity'].search([
            ('activity_type_id', '=', self.activity_type_warn_id),
            ('res_id', '=', base_exception.line_ids[0].id),
            ('user_id', '=', self.user_demo.id),
            ('summary', '=', 'File type unknown!'),
        ])
        self.assertEquals(len(mail_activities), 1)
        self.generate_empty_file('beezup_es_ES.lock')
        params = {
            'file_type': 'standard',
            'company_id': self.company.id,
            'lang': 'es_ES',
        }
        base_exception = self.create_base_exception(
            'beezup_generate_file', params, 'schedule_activity_exception',
            self.company.id)
        base_exception.line_ids.run()
        mail_activities = self.env['mail.activity'].search([
            ('activity_type_id', '=', self.activity_type_warn_id),
            ('res_id', '=', base_exception.line_ids[0].id),
            ('user_id', '=', self.user_demo.id),
            ('summary', '=', 'Process generatte file running...'),
        ])
        self.assertEquals(len(mail_activities), 1)

    def test_beezup_image_get_without_image(self):
        self.product1.product_tmpl_id.write({
            'image': None,
            'product_image_ids': [(6, 0, [])],
        })
        self.assertFalse(self.product1.product_tmpl_id.image)
        self.assertFalse(self.product1.product_tmpl_id.product_image_ids)
        params = {
            'product_id': self.product1.id,
        }
        base_exception = self.create_base_exception(
            'image_get', params, 'schedule_activity_exception',
            self.company.id)
        base_exception.line_ids.notify_exception = False
        base_exception.line_ids.run()
        mail_activities = self.env['mail.activity'].search([
            ('activity_type_id', '=', self.activity_type_warn_id),
            ('res_id', '=', base_exception.line_ids[0].id),
            ('user_id', '=', self.user_demo.id),
        ])
        self.assertFalse(mail_activities)
