###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http, tools
from odoo.http import request, STATIC_CACHE
from odoo.addons.web.controllers import main
import hashlib


class Binary(main.Binary):

    def image_disk_allowed_model(self, model):
        allowed_models = [
            'product.template',
            'product.product',
            'product.image',
            'product.image.transient']
        if model not in allowed_models:
            return None
        if model == 'product.image':
            return 'product.image.transient'
        return model

    @http.route([
        '/web/image',
        '/web/image/<string:xmlid>',
        '/web/image/<string:xmlid>/<string:filename>',
        '/web/image/<string:xmlid>/<int:width>x<int:height>',
        '/web/image/<string:xmlid>/<int:width>x<int:height>/<string:filename>',
        '/web/image/<string:model>/<int:id>/<string:field>',
        '/web/image/<string:model>/<int:id>/<string:field>/<string:filename>',
        ('/web/image/<string:model>/<int:id>/<string:field>/'
         '<int:width>x<int:height>'),
        ('/web/image/<string:model>/<int:id>/<string:field>/'
         '<int:width>x<int:height>/<string:filename>'),
        '/web/image/<int:id>',
        '/web/image/<int:id>/<string:filename>',
        '/web/image/<int:id>/<int:width>x<int:height>',
        '/web/image/<int:id>/<int:width>x<int:height>/<string:filename>',
        '/web/image/<int:id>-<string:unique>',
        '/web/image/<int:id>-<string:unique>/<string:filename>',
        '/web/image/<int:id>-<string:unique>/<int:width>x<int:height>',
        ('/web/image/<int:id>-<string:unique>/<int:width>x<int:height>/'
         '<string:filename>')],
        type='http', auth="public", website=True)
    def content_image(self, xmlid=None, model='ir.attachment', id=None,
                      field='datas', filename_field='datas_fname', unique=None,
                      filename=None, mimetype=None, download=None, width=0,
                      height=0, crop=False, access_token=None):
        allowed_model = self.image_disk_allowed_model(model)
        if not allowed_model:
            return super(Binary, self).content_image(
                xmlid, model, id, field, filename_field, unique, filename,
                mimetype, download, width, height, crop, access_token)
        sizes = {
            'image_big': (1024, 1024),
            'image_medium': (128, 128),
            'image_small': (64, 64)}
        size = sizes.get(field, (width, height))
        if not size:
            size = (64, 64)
        record = request.env[allowed_model].with_context(
            website=request.website.id).browse(int(id))
        content, mime = request.website.image_get(
            record.name_slug, size=size, crop=crop)
        if not content:
            return request.not_found()
        headers = [
            ('Content-Length', len(content)),
            ('Content-Type', mime),
            ('X-Content-Type-Options', 'nosniff'),
            ('Cache-Control', 'max-age=%s' % (unique and STATIC_CACHE or 0))]
        status = 200
        if bool(request) and 'If-None-Match' in request.httprequest.headers:
            etag = request.httprequest.headers.get('If-None-Match')
            content_utf8 = tools.pycompat.to_text(content).encode('utf-8')
            retag = '"%s"' % hashlib.md5(content_utf8).hexdigest()
            headers.append('ETag', retag)
            status = etag == retag and 304 or 200
        response = request.make_response(content, headers)
        response.status_code = status
        return response
