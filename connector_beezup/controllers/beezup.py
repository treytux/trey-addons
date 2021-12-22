###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import logging
from io import StringIO

from odoo import http
from odoo.http import request

_log = logging.getLogger(__name__)

try:
    import pandas as pd
except (ImportError, IOError) as err:
    _log.debug(err)


class Beezup(http.Controller):

    def select_db(self):
        db = request.params.get('db') and request.params.get('db').strip()
        if db and db not in http.db_filter([db]):
            db = None
        request.session.db = db

    @http.route([
        '/beezup/csv/last/<string:file_type>',
        '/beezup/csv/last/<string:file_type>/<int:company_id>',
        '/beezup/csv/last/<string:file_type>/<string:lang>',
        '/beezup/csv/last/<string:file_type>/<string:lang>/<int:company_id>',
    ], type='http', auth='none', sitemap=False)
    def beezup_last(self, file_type, lang=None, company_id=None, db=None):
        self.select_db()
        env = request.env
        if not lang:
            lang = env.user.lang
        if not company_id:
            company_id = env.user.company_id.id
        df = env['product.product'].sudo().beezup_get_file_last(file_type, lang)
        file_not_exists = (
            isinstance(df, pd.DataFrame) and len(df) < 1
            or isinstance(df, bool) and df is False)
        if file_not_exists:
            _log.info('Beezup file not exist, generate it')
            fname, df = env['product.product'].sudo().beezup_generate_file(
                file_type, lang=lang, company_id=company_id)
        buffer = StringIO()
        df.to_csv(buffer, header=True, index=False, sep=';')
        return request.make_response(buffer.getvalue(), {
            'Content-Disposition': 'inline; filename="beezup_%s.csv"' % lang,
            'Content-Type': 'text/csv',
        })

    @http.route([
        '/beezup/csv/<string:file_type>/<int:company_id>/<string:lang>/'
        '<int:limit>/<int:offset>',
        '/beezup/csv/<string:file_type>/<int:company_id>/<string:lang>/'
        '<int:limit>',
        '/beezup/csv/<string:file_type>/<int:company_id>/<string:lang>',
        '/beezup/csv/<string:file_type>/<int:company_id>',
        '/beezup/csv/<string:file_type>/<string:lang>/<int:limit>/'
        '<int:offset>',
        '/beezup/csv/<string:file_type>/<string:lang>/<int:limit>',
        '/beezup/csv/<string:file_type>/<string:lang>',
        '/beezup/csv/<string:file_type>',
    ], type='http', auth='none', website=True)
    def beezup_csv(
            self, file_type, lang=None, limit=None, offset=0, company_id=None,
            db=None):
        self.select_db()
        env = request.env
        if not lang:
            lang = env.user.lang
        if not company_id:
            company_id = env.user.company_id.id
        fname, df = env['product.product'].sudo().beezup_generate_file(
            file_type, lang=lang, limit=limit, offset=offset,
            company_id=company_id)
        buffer = StringIO()
        df.to_csv(buffer, header=True, index=False, sep=';')
        return request.make_response(buffer.getvalue(), {
            'Content-Disposition': 'inline; filename="beezup_%s.csv"' % lang,
            'Content-Type': 'text/csv',
        })

    @http.route([
        '/beezup/image/<int:product_id>',
        '/beezup/image/<int:product_id>/<int:index>',
    ], type='http', auth='none', website=True)
    def beezzup_image_get(self, product_id, index=0, db=None):
        self.select_db()
        env = request.env
        image = env['product.product'].sudo().image_get(product_id, index)
        headers = [('Content-Type', 'image/png')]
        status = 200
        image_base64 = base64.b64decode(image)
        headers.append(('Content-Length', len(image_base64)))
        response = request.make_response(image_base64, headers)
        response.status = str(status)
        return response
