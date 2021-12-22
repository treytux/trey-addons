###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import logging
import os
from os import listdir
from os.path import isfile, join

from odoo import api, models, tools

_log = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def cron_product_template_import_images_from_folder(self):
        product_tmpl_obj = self.env['product.template']
        path = os.path.join(
            tools.config.filestore(self.env.cr.dbname), 'images2import')
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        files = [f for f in listdir(path) if isfile(join(path, f))]
        templates = {}
        for file in files:
            try :
                key = file.split('.')[0]
                item = templates.setdefault(int(key.split('-')[0]), [])
            except Exception:
                _log.warning(
                    'File %s not has prefix integer with product template' % (
                        file))
                continue
            item.append(file)
        for index, template_id in enumerate(templates.keys()):
            template = product_tmpl_obj.browse(template_id)
            if not template.exists():
                _log.warning(
                    '[%s/%s](IGNORE) Product template ID %s not exists' % (
                        index + 1, len(templates), template_id))
                continue
            files = templates[template_id]
            if not files:
                continue
            files.sort()
            file = files.pop()
            with open(join(path, file), 'rb') as fp:
                try:
                    template.image = base64.encodestring(fp.read())
                except Exception as ex:
                    _log.error('Image %s with problems: %s' % (file, ex))
                    self.env.cr.rollback()
                    continue
            self.env.cr.commit()
            os.remove(join(path, file))
            _log.info('[%s/%s] Product template ID %s update' % (
                index + 1, len(templates), template.id))
            if not files or 'product_image_ids' not in template._fields:
                continue
            template.product_image_ids.unlink()
            for file in files:
                try:
                    with open(join(path, file), 'rb') as fp:
                        template.product_image_ids.create({
                            'image': base64.encodestring(fp.read()),
                            'product_tmpl_id': template.id,
                        })
                except Exception as ex:
                    _log.error('Image %s with problems: %s' % (file, ex))
                    self.env.cr.rollback()
                    continue
            else:
                self.env.cr.commit()
                os.remove(join(path, file))
