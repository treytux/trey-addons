###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import logging
import os

import pandas as pd
from odoo import api, fields, models
from odoo.tools import config

_log = logging.getLogger('EDE image load')


class ResCompany(models.Model):
    _inherit = 'res.company'

    def _default_image_path(self):
        return '%s/%s' % (config.get('data_dir'), '/filestore/ede_images')

    ede_image_limit = fields.Integer(
        string='Image limit',
        required=True,
        default=100,
    )
    ede_image_path = fields.Char(
        string='Images path',
        required=True,
        default=_default_image_path,
    )

    @api.multi
    def ede_image_import(self, df=None, limit=100):
        ede_image_path = self.env.user.company_id.ede_image_path
        ede_supplier = self.env.user.company_id.ede_supplier_id
        df = df.head(limit)
        for index, row in df.iterrows():
            templates = self.env['product.template'].search([
                '|', '|', '|',
                ('default_code', 'ilike', row['KEYWORKD_1']),
                ('default_code', 'ilike', row['KEYWORKD_2']),
                ('default_code', 'ilike', row['KEYWORKD_3']),
                ('barcode', 'ilike', row['EAN']),
            ])
            if not templates:
                _log.error('No product for image: %s product EAN: %s' % (
                    row['MIME_SOURCE'], row['EAN']))
                continue
            supplier_infos = templates.mapped('seller_ids').filtered(
                lambda s: s.name.id == ede_supplier.id)
            if not supplier_infos:
                continue
            template = supplier_infos[0].product_tmpl_id
            if row['MIME_PURPOSE'] == 'logo':
                icon = self.env['product.icon'].search([
                    ('name', '=', row['MIME_SOURCE'])])
                if not icon:
                    img = open(os.path.join(
                        ede_image_path, 'images', row['MIME_SOURCE']), 'rb')
                    icon = self.env['product.icon'].create({
                        'name': row['MIME_SOURCE'],
                        'image': base64.standard_b64encode(img.read()),
                    })
                if template.mapped('icon_ids').filtered(
                        lambda l: l.icon_id.name == row['MIME_SOURCE']):
                    continue
                self.env['product.template.icon'].create({
                    'sequence': int(row['MIME_ORDER']),
                    'icon_id': icon.id,
                    'product_template_id': template.id,
                })
            elif row['MIME_PURPOSE'] == 'normal':
                if template.image:
                    continue
                img = open(os.path.join(
                    ede_image_path, 'images', row['MIME_SOURCE']), 'rb')
                template.write({
                    'image': base64.standard_b64encode(img.read()),
                })
            else:
                if template.mapped('product_image_ids').filtered(
                        lambda i: i.name == row['MIME_SOURCE']):
                    continue
                img = open(os.path.join(
                    ede_image_path, 'images', row['MIME_SOURCE']), 'rb')
                self.env['product.image'].create({
                    'name': row['MIME_SOURCE'],
                    'image': base64.standard_b64encode(img.read()),
                    'product_tmpl_id': template.id,
                })
            _log.info(
                '[%s/%s] Load image: %s product_template: %s type: %s' % (
                    index + 1, len(df), row['MIME_SOURCE'],
                    template.id, row['MIME_PURPOSE']
                )
            )
        return True

    @api.model
    def cron_ede_image_import_process(self):
        if not self.env.user.company_id.ede_image_path:
            _log.info('Please configure EDE images directory in company setup')
            return
        file_path = os.path.join(
            self.env.user.company_id.ede_image_path, 'ede_images.csv')
        image_limit = self.env.user.company_id.ede_image_limit
        try:
            images_df = pd.read_csv(file_path, error_bad_lines=False, sep=';')
        except Exception as e:
            _log.error('Could not open file: %s' % e)
            return
        _log.info(
            'Start load EDE supplier images process %s lines from %s total' % (
                image_limit, len(images_df)
            )
        )
        terminate = self.ede_image_import(images_df, image_limit)
        if terminate:
            images_df = images_df.iloc[image_limit:]
            images_df.to_csv(file_path, index=False, sep=';')
        else:
            _log.info('error process is not finished')
        _log.info('End load EDE supplier images')
