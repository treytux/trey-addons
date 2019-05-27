###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models, api, tools
import base64
import mimetypes
import os
import re
import logging
_log = logging.getLogger(__name__)


class Website(models.Model):
    _inherit = 'website'

    image_slug_path = fields.Char(
        string='Image slug path',
        default='/odoo-image-slug')
    image_slug_translate = fields.Boolean(
        string='Image slug translate')

    @api.model
    def default_website_get(self):
        website_id = self.env.context.get('website')
        return (
            website_id and
            self.env['website'].browse(website_id) or
            self.env['website'].search([], limit=1))

    @api.multi
    def image_path(self, *args):
        self.ensure_one()
        return os.path.join(self.image_slug_path, *args)

    @api.multi
    def image_path_size(self, fname, size=None, crop=False):
        if not size:
            size = [None, None]
        self.ensure_one()
        folder = ''
        if any(size):
            folder = '%sx%s%s' % (size[0], size[1], crop and '-crop' or '')
            if not os.path.exists(self.image_path(folder)):
                os.mkdir(self.image_path(folder))
        return self.image_path(folder, os.path.basename(fname))

    @api.multi
    def image_get(self, slug, size=None, crop=False):
        if not size:
            size = [None, None]
        files = self.image_files_get(slug)
        if not files:
            return ('', False)
        return self.image_content_get(files[0], size=size, crop=crop)

    @api.multi
    def image_files_get(self, slug):
        self.ensure_one()
        if os.path.exists(self.image_path(slug, slug)):
            return [slug]
        if not os.path.exists(self.image_slug_path):
            _log.error(
                'Not exists image slug path "%s"' % self.image_slug_path)
            return []
        if not os.path.exists(self.image_path(slug)):
            return []
        if not os.path.isdir(self.image_path(slug)):
            return [slug]
        regexp = r'(?i)%s[-]?(?:\d+)?(?:\.jpg|\.jpeg|\.png|\.gif)' % slug
        return sorted([
            os.path.join(slug, f) for f in os.listdir(self.image_path(slug))
            if re.search(regexp, f) and
            os.path.isfile(self.image_path(slug, f))])

    @api.multi
    def image_content_get(self, fname, size=None, crop=False):
        def is_new(new, old):
            return os.stat(new).st_mtime > os.stat(old).st_mtime

        if not size:
            size = [None, None]
        self.ensure_one()
        file = self.image_path(fname)
        if not any(size):
            return (
                os.path.exists(file) and
                self._image_content_from_disk(file) or
                self._image_content_from_memory(file))
        file_size = self.image_path_size(fname, size=size, crop=crop)
        if os.path.exists(file_size) and is_new(file_size, file):
            return self._image_content_from_disk(file_size)
        else:
            return self._image_content_from_memory(file, size, crop)

    @api.multi
    def _image_content_from_disk(self, file):
        self.ensure_one()
        if not os.path.exists(file) or not os.path.isfile(file):
            return (None, None)
        mime = mimetypes.guess_type(file)[0]
        with open(file, 'rb') as fp:
            content = fp.read()
        return (content, mime)

    @api.multi
    def _image_content_from_memory(self, file, size=None, crop=False):
        if not size:
            size = [None, None]
        self.ensure_one()
        mime = any(size) and mimetypes.guess_type(file)[0] or 'image/png'
        with open(file, 'rb') as fp:
            content = fp.read()
        if crop and any(size):
            content_b64 = base64.b64encode(content)
            content_b64 = tools.crop_image(
                content_b64, type='center', size=size, ratio=(1, 1))
            content = base64.b64decode(content_b64)
        elif any(size):
            content_b64 = base64.b64encode(content)
            content_b64 = tools.image_resize_image(
                base64_source=content_b64, size=size, encoding='base64',
                filetype='PNG')
            content = base64.b64decode(content_b64)
        if any(size):
            file = self.image_path_size(os.path.basename(file), size, crop)
            with open(file, 'wb') as fp:
                fp.write(content)
            _log.info('Image file %s created' % file)
        return (content, mime)
