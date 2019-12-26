# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import base64
import glob
import os
from cStringIO import StringIO
from openerp import http
from openerp.http import request
from PIL import Image
import logging
_log = logging.getLogger(__name__)

FILE_TYPES = ('.jpg', '.jpeg', '.png', '.gif')


def get_static_dir():
    static_dir = request.env['ir.config_parameter'].get_param(
        'website_sale_multi_image_disk.static_dir')
    if static_dir and static_dir != 'None':
        return static_dir
    addon = 'website_sale_multi_image_disk'
    manifest = http.addons_manifest.get(addon, None)
    addons_path = manifest.get('addons_path', None)
    return ('' if not addons_path else os.path.join(
        addons_path, addon, 'static', 'images'))


def get_disk_images(slug):
    folder_by_product = eval(request.env['ir.config_parameter'].get_param(
        'website_sale_multi_image_disk.folder_by_product'))
    path = (
        folder_by_product and os.path.join(os.path.join(
            get_static_dir(), slug), slug) or os.path.join(
            get_static_dir(), slug))
    images = []
    for ft in FILE_TYPES:
        files = glob.glob('%s-[0-9]%s' % (path, ft))
        images.extend([os.path.basename(f) for f in files])
    images.sort()
    return images


def create_disk_image(source, target, width, height, quality=False):
    method = getattr(Image, 'ANTIALIAS')
    source_file = Image.open(source)
    target_file = source_file.copy()
    target_file.convert('RGB')
    target_width = target_file.size[0]
    target_height = target_file.size[1]
    portrait = target_width <= target_height
    w = (height * target_width / target_height if portrait else width)
    h = (height if portrait else width * target_height / target_width)
    target_file.thumbnail((w, h), method)
    target_file.save(
        target, 'JPEG', quality=(not quality and int(request.env[
            'ir.config_parameter'].get_param(
                'website_sale_multi_image_disk.image_quality')) or quality))


def send_file(path):
    image_base64 = base64.b64encode(open(path, 'rb').read())
    image_data = StringIO(str(image_base64).decode('base64'))
    return http.send_file(image_data, mimetype='image/jpeg')


def get_disk_image(filename, max_width=None, max_height=None):
    folder_by_product = eval(request.env['ir.config_parameter'].get_param(
        'website_sale_multi_image_disk.folder_by_product'))
    if folder_by_product:
        sub_name = ((filename.split('.')[0]).split('-'))
        sub_name.pop(-1)
        path = os.path.join(os.path.join(
            get_static_dir(), '-'.join(sub_name), filename))
    else:
        path = os.path.join(get_static_dir(), filename)
    thumb_path = None
    if max_width and max_height:
        thumb_dir = os.path.join(
            get_static_dir(), '%sx%s' % (max_width, max_height))
        if not os.path.exists(thumb_dir):
            os.makedirs(thumb_dir)
        thumb_path = os.path.join(thumb_dir, filename)
    if os.path.exists(path):
        try:
            if not thumb_path:
                return send_file(path)
            if os.path.exists(thumb_path):
                if os.stat(path).st_mtime > os.stat(thumb_path).st_mtime:
                    create_disk_image(
                        path, thumb_path, max_width, max_height)
                    if os.path.exists(thumb_path):
                        return send_file(thumb_path)
                return send_file(thumb_path)
            create_disk_image(
                path, thumb_path, max_width, max_height)
            if os.path.exists(thumb_path):
                return send_file(thumb_path)
        except Exception as e:
            _log.warning('Can not open file %s, error: %s', path, e)
    else:
        _log.warning('File %s not found', path)
