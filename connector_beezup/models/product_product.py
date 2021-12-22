###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging
import os
import time
from datetime import datetime

import werkzeug
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import config

_log = logging.getLogger(__name__)

try:
    import pandas as pd
except (ImportError, IOError) as err:
    _log.debug(err)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    export_to_beezup = fields.Boolean(
        string='Export to Beezup',
    )

    @api.multi
    def unlink(self):
        company = self.env.user.company_id
        for product in self:
            if not company.beezup_product_ids2delete:
                company.beezup_product_ids2delete = str(product.id)
            else:
                company.beezup_product_ids2delete = (
                    '%s' % ', '.join(
                        [company.beezup_product_ids2delete, str(product.id)]))
        return super().unlink()

    def init(self):
        path = config.filestore(self.env.cr.dbname)
        for file in os.listdir(path):
            if not file.endswith('.lock'):
                continue
            _log.info('Remove lock file %s' % os.path.join(path, file))
            os.remove(os.path.join(path, file))

    def dataframe_get(self, fname, file_type):
        ext = fname.split('.')[-1:][0]
        if ext in ['csv']:
            try:
                df = pd.read_csv(
                    fname, encoding='utf-8', na_values=['NULL'], sep=';',
                    converters=self.get_columns2convert(file_type))
            except pd.errors.EmptyDataError:
                df = pd.DataFrame()
        else:
            raise UserError(_('File extension must be \'csv\'.'))
        return df.where((pd.notnull(df)), None)

    def get_columns2convert(self, file_type):
        if file_type == 'standard':
            cols2str = ['barcode', 'default_code', 'name']
        elif file_type == 'update_stock':
            cols2str = ['barcode', 'name']
        return dict.fromkeys(cols2str, str)

    def get_price(self, pricelist):
        return self.with_context(pricelist=pricelist).list_price

    def set_url_domain(self, company_id=None):
        if not company_id:
            company_id = self.env.user.company_id.id
        company = self.env['res.company'].browse(company_id)
        domain = (
            self.env['ir.config_parameter'].get_param('beezup.url')
            or self.env['ir.config_parameter'].get_param('web.base.url')
        )
        if domain:
            company.beezup_domain = domain
        else:
            raise UserError(_(
                'Could not get domain for Beezup connector from configuration '
                'parameters.'))

    def get_file_name(self, file_type, lang, extension):
        assert lang != '', 'lang param must be fill.'
        if file_type == 'standard':
            file_name = 'beezup_%s.%s' % (lang, extension)
        elif file_type == 'update_stock':
            file_name = 'beezup_%s_update_stock.%s' % (lang, extension)
        else:
            raise UserError(_('File type unknown!'))
        return file_name

    def beezup_get_file_last(self, file_type, lang=None):
        if not lang:
            lang = self.env.user.lang
        file_name = self.get_file_name(file_type, lang, 'csv')
        fname = os.path.join(config.filestore(self.env.cr.dbname), file_name)
        if not os.path.exists(fname):
            return False
        return self.dataframe_get(fname, file_type)

    def beezeup_lock_remove(self, file_type, lang):
        file_name = self.get_file_name(file_type, lang, 'lock')
        lock_fname = os.path.join(
            config.filestore(self.env.cr.dbname), file_name)
        _log.info('Remove lock file %s' % lock_fname)
        os.remove(lock_fname)

    def _check_generate_beezup_file(self, fname):
        if os.path.exists(fname):
            local = time.localtime(os.path.getmtime(fname))
            if time.localtime().tm_yday == local.tm_yday:
                hour = time.localtime().tm_hour
                if hour + 2 < local.tm_hour:
                    _log.info('Lock file %s older' % fname)
                    return True
            _log.info('Lock file %s exists, ignore generation' % fname)
            return False
        return True

    def beezeup_lock(self, lang, file_type):
        file_name = self.get_file_name(file_type, lang, 'lock')
        fname = os.path.join(config.filestore(self.env.cr.dbname), file_name)
        if self._check_generate_beezup_file(fname):
            open(fname, 'w').write('Running...')
            return True
        return False

    @api.model
    def beezup_generate_file(
            self, file_type, lang=None, limit=None, offset=0, company_id=None):
        self.set_url_domain(company_id)
        if not lang:
            lang = self.env.user.lang
        if not company_id:
            company_id = self.env.user.company_id.id
        if not self.beezeup_lock(lang, file_type):
            raise UserError(_('Process generatte file running...'))
        file_name = self.get_file_name(file_type, lang, 'csv')
        fname = os.path.join(config.filestore(self.env.cr.dbname), file_name)
        if os.path.exists(fname):
            fname, df_content = self.update_file(
                fname, file_type, lang, limit, offset, company_id)
        else:
            fname, df_content = self.generate_file(
                None, file_type, lang, limit, offset, company_id)
        return fname, df_content

    def products2create_domain(self, company_id):
        return [
            '|',
            ('company_id', '=', company_id),
            ('company_id', '=', None),
            ('active', '=', 'True'),
            ('sale_ok', '=', 'True'),
            ('export_to_beezup', '=', 'True'),
        ]

    def get_products2create(
            self, date_update, file_type, lang, limit, offset, company_id):
        if file_type == 'standard':
            domain = self.products2create_domain(company_id)
            product_obj = self.env['product.product']
            return product_obj.with_context(lang=lang).search(
                domain, limit=limit, offset=offset)
        elif file_type == 'update_stock':
            move_domain = [
                '|',
                ('company_id', '=', company_id),
                ('company_id', '=', None),
                ('state', '=', 'done'),
                ('product_id.export_to_beezup', '=', 'True'),
            ]
            if date_update:
                move_domain.append(('write_date', '>=', date_update))
            move_obj = self.env['stock.move']
            moves = move_obj.with_context(lang=lang).search(
                move_domain, limit=limit, offset=offset)
            return moves.mapped('product_id')

    def products2update_domain(self, date_update, company_id):
        domain = [
            '|',
            ('company_id', '=', company_id),
            ('company_id', '=', None),
            ('active', '=', 'True'),
            ('sale_ok', '=', 'True'),
            ('export_to_beezup', '=', 'True'),
        ]
        if date_update:
            domain.append(('write_date', '>=', date_update))
        return domain

    def get_products2update(
            self, date_update, file_type, lang, limit, offset, company_id):
        move_domain = [
            '|',
            ('company_id', '=', company_id),
            ('company_id', '=', None),
            ('state', '>=', 'done'),
            ('product_id.export_to_beezup', '=', 'True'),
        ]
        if date_update:
            move_domain.append(('write_date', '>=', date_update))
        move_obj = self.env['stock.move']
        moves = move_obj.with_context(lang=lang).search(
            move_domain, limit=limit, offset=offset)
        products_stock_changed = moves.mapped('product_id')
        if file_type == 'standard':
            domain = self.products2update_domain(date_update, company_id)
            product_obj = self.env['product.product']
            products = product_obj.with_context(lang=lang).search(
                domain, limit=limit, offset=offset)
            return products + products_stock_changed
        elif file_type == 'update_stock':
            return products_stock_changed

    def generate_file(
            self, date_update, file_type, lang=None, limit=None, offset=0,
            company_id=None):
        products = self.get_products2create(
            date_update, file_type, lang, limit, offset, company_id)
        try:
            df_content = products.beezup_csv_file_get(file_type, company_id)
            if limit is None:
                file_name = self.get_file_name(file_type, lang, 'csv')
                fname = os.path.join(
                    config.filestore(self.env.cr.dbname), file_name)
                df_content.to_csv(fname, header=True, index=False, sep=';')
                _log.info('File Beezup %s created' % fname)
            return (fname, df_content)
        finally:
            self.beezeup_lock_remove(file_type, lang)

    def update_rows(self, file_type, df, product_ids, company_id):
        products2update_file = []
        for index, row in df.iterrows():
            if row['id'] in product_ids:
                product = self.env['product.product'].browse(row['id'])
                vals = product._beezup_csv_row_get(file_type, company_id)
                if not vals:
                    _log.warn('Product without price: %s' % product.name)
                    continue
                for key in vals.keys():
                    df.loc[index, key] = vals.get(key)
                _log.info('Updated product \'%s\' (id=%s)' % (
                    product.name, row['id']))
                products2update_file.append(row['id'])
        return products2update_file

    def create_rows(self, file_type, df, products2create_file, company_id):
        for index, product_id in enumerate(products2create_file):
            _log.info('[%s/%s] Beezup updated CSV file' % (
                index + 1, len(self)))
            product = self.env['product.product'].browse(product_id)
            vals = product._beezup_csv_row_get(file_type, company_id)
            if not vals:
                _log.warn('Product without price: %s' % product.name)
                continue
            new_index = index + len(df)
            for key in vals.keys():
                df.loc[new_index, key] = vals.get(key)

    def unlink_rows(self, df, company_id=None):
        if not company_id:
            company_id = self.env.user.company_id.id
        company = self.env['res.company'].browse(company_id)
        product_ids_str = company.beezup_product_ids2delete
        if not product_ids_str:
            return df
        index2delete = []
        product_ids = [int(n) for n in list(product_ids_str.split(', '))]
        for index, row in df.iterrows():
            if row['id'] in product_ids:
                _log.info(
                    'Deleted product id=%s index %s' % (row['id'], index))
                index2delete.append(index)
        df_updated = df.drop(index2delete)
        company.beezup_product_ids2delete = ''
        return df_updated

    def update_file(
            self, fname, file_type, lang=None, limit=None, offset=0,
            company_id=None):
        if not company_id:
            company_id = self.env.user.company_id.id
        date_update = datetime.fromtimestamp(os.path.getmtime(fname))
        products = self.get_products2update(
            date_update, file_type, lang, limit, offset, company_id)
        try:
            df = self.dataframe_get(fname, file_type)
            products2update_file = self.update_rows(
                file_type, df, products.ids, company_id)
            products2create_file = list(
                set(products.ids) - set(products2update_file))
            self.create_rows(file_type, df, products2create_file, company_id)
            df = self.unlink_rows(df, company_id)
            return (fname, df)
        finally:
            self.beezeup_lock_remove(file_type, lang)

    @api.multi
    def beezup_csv_file_get(self, file_type, company_id=None):
        def parse_val(val):
            if val is None or val is False:
                return ''
            if isinstance(val, str):
                return val.encode('utf-8')
            return val

        rows = []
        for index, product in enumerate(self):
            _log.info(
                '[%s/%s] Beezup generate CSV file' % (
                    index + 1, len(self)))
            vals = product._beezup_csv_row_get(file_type, company_id)
            if not vals:
                continue
            rows.append(vals)
        return pd.DataFrame(rows)

    @api.multi
    def _beezup_csv_row_get(self, file_type, company_id=None):

        def stock_web_get(product, company_id):
            lines = self.env['sale.order.line'].read_group(
                [
                    '|',
                    ('company_id', '=', company_id),
                    ('company_id', '=', None),
                    ('product_id', '=', product.id),
                    ('state', '=', 'confirmed'),
                ],
                ['product_uom_qty', 'product_id', 'state'],
                []
            )
            total = [
                ln['product_uom_qty'] for ln in lines if ln['product_uom_qty']]
            if total:
                return product.qty_available - sum(total)
            return product.qty_available

        self.ensure_one()
        if not company_id:
            company_id = self.env.user.company_id.id
        company = self.env['res.company'].browse(company_id)
        stock_web = stock_web_get(self, company_id)
        stock_web = stock_web < 1 and 0 or stock_web
        vals = {'custom_%s' % c.name: c.value for c in self.custom_info_ids}
        pricelist = company.beezup_pricelist_id
        if not pricelist:
            raise UserError(_(
                'You must fill \'Beezup pricelist\' field from your '
                'company in Settings/Company menuitem in Conector Beezup.')
            )
        price = self.get_price(pricelist)
        if not price:
            return False
        if file_type == 'standard':
            vals.update({
                'id': self.id,
                'name': self.name,
                'barcode': self.barcode,
                'customer_price': round(price, 2),
                'weight': self.weight,
                'qty_available': (
                    self.qty_available < 0 and 0 or int(self.qty_available)),
                'stock_web': stock_web,
                'default_code': self.default_code,
                'category': ', '.join([c.name for c in self.public_categ_ids]),
            })
        elif file_type == 'update_stock':
            vals.update({
                'id': self.id,
                'name': self.name,
                'barcode': self.barcode,
                'customer_price': round(price, 2),
                'category': ', '.join([c.name for c in self.public_categ_ids]),
                'qty_available': (
                    self.qty_available < 0 and 0 or int(self.qty_available)),
            })
        domain = company.beezup_domain
        suffix = (
            '?db=%s' % self.env.cr.dbname
            if 'connector_beezup' in config.get('server_wide_modules', '')
            else '')
        if self.image:
            vals['image_0'] = '%s/beezup/image/%s/%s%s' % (
                domain, self.id, 0, suffix)
        for index, _image in enumerate(self.product_image_ids):
            vals['image_%s' % str(index + 1)] = '%s/beezup/image/%s/%s%s' % (
                domain, self.id, index + 1, suffix)
        return vals

    @api.model
    def image_get(self, product_id, index=0):
        product = self.env['product.product'].browse(product_id)
        if not product:
            raise werkzeug.exceptions.NotFound()
        if index == 0:
            image = product.image
        else:
            try:
                image = product.product_image_ids[index].image
            except Exception:
                raise werkzeug.exceptions.NotFound()
        if not image:
            return ''
        return image
