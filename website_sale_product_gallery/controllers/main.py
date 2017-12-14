# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

import os
import cStringIO
import datetime
import hashlib

from openerp import http, SUPERUSER_ID
from openerp.tools import misc
from openerp.http import request
from openerp.addons.website_sale_product_gallery.models.gallery_image \
    import _filestorage
from werkzeug.wrappers import Response
from PIL import Image
from sys import maxint

import logging
_log = logging.getLogger(__name__)


class GalleryImage(http.Controller):

    def __init__(self, *args, **kwargs):
        super(GalleryImage, self).__init__(*args, **kwargs)
        self.models_gallery = None

    def _get_image_gallery(self, slug):
        if self.models_gallery is None:
            # regeneramos la cache de modelos de galerias
            self.models_gallery = [model for model_name, model in
                                   request.registry.models.items()
                                   if model_name.rfind('.gallery_image') != -1]

        # buscamos slug en los diferentes modelos de imagenes
        for model in self.models_gallery:
            img = model.search(request.cr, SUPERUSER_ID, [('name', '=', slug)])
            if img:
                return img, model
        return None, None

    @http.route(['/images/<slug>',
                 '/images/<int:max_width>x<int:max_height>/<slug>'],
                type='http', auth='public')
    def images(self, slug, max_width=None, max_height=None, *args, **kwargs):
        cr, context = request.cr, request.context

        # buscamos imagen por slug
        img, model = self._get_image_gallery(slug)
        if not img:
            return request.not_found()

        # leemos imagen
        [record] = model.read(
            cr, SUPERUSER_ID, [img[0]],
            ['name', 'last_update_img'], context=context)

        path_file = os.path.join(_filestorage(cr), record.get('name'))
        if not path_file:
            return request.not_found()

        # generamos respuesta
        server_format = misc.DEFAULT_SERVER_DATETIME_FORMAT
        response = Response(mimetype='image/jpg')
        response.last_modified = datetime.datetime.strptime(
            record.get('last_update_img'), server_format)
        response.make_conditional(request.httprequest)
        if response.status_code == 304:
            return response

        # si no hay tamaño la original
        if (not max_width) and (not max_height):
            data = self._read_image_data(path_file)
            response.set_etag(hashlib.sha1(data).hexdigest())
            response.data = data
            return response

        # creamos thumb si no existe
        path, file_name = os.path.split(path_file)
        path_file_thumb = os.path.join(path,
                                       '{}x{}'.format(max_width, max_height))
        if not os.path.exists(path_file_thumb):
            try:
                os.makedirs(path_file_thumb)
            except:
                _log.error(
                    'ERROR creando directorio para galerias <%s>' % slug)
                return response

        path_file_thumb = os.path.join(path_file_thumb, file_name)
        if os.path.exists(path_file_thumb):
            data = self._read_image_data(path_file_thumb)
            response.set_etag(hashlib.sha1(data).hexdigest())
            response.data = data
            return response

        # creamos thumb
        data = self._read_image_data(path_file)
        response.set_etag(hashlib.sha1(data).hexdigest())
        image = Image.open(cStringIO.StringIO(data))
        response.mimetype = Image.MIME[image.format]

        w, h = image.size
        max_w = int(max_width) if max_width else maxint
        max_h = int(max_height) if max_height else maxint

        # guardamos en disco
        image.thumbnail((max_w, max_h), Image.ANTIALIAS)
        image.save(path_file_thumb, image.format)

        response.data = self._read_image_data(path_file_thumb)

        return response

    def _read_image_data(self, path_file):
        try:
            with open(path_file, 'rb') as f:
                return f.read()
        except:
            path = os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(path, '..', 'static', 'src', 'img',
                                'error.png')

            with open(path, 'rb') as f:
                return f.read()

    @http.route(['/images/xhr/product/<model("product.product"):product>',
                 '/images/xhr/tmpl/<model("product.template"):product_tmpl>'],
                type='json', auth="public", methods=['POST'], website=True)
    def image_ajax(self, product=None, product_tmpl=None):
        """
        Devuelve el nombre de la imagen para el producto pedido
        """
        if product:
            gallery = request.registry['ir.ui.view'].get_gallery(product)
        else:
            gallery = request.registry['ir.ui.view'].get_gallery(product_tmpl)

        return [g.name for g in gallery]
