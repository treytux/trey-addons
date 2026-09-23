###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import re
from datetime import datetime, timedelta
from functools import partial

from odoo import fields, http
from odoo.http import request

DATE_FORMAT = '%Y-%m-%d %H:%M'
FEED_MIMETYPE = 'application/xml; charset=utf-8'


class GoogleShopping(http.Controller):

    def get_effective_date(self, date_start, date_end):
        if not date_start or not date_end:
            return ''
        if isinstance(date_start, str):
            ds = datetime.strptime(date_start, '%Y-%m-%d %H:%M:%S')
        else:
            ds = date_start
        if isinstance(date_end, str):
            de = datetime.strptime(date_end, '%Y-%m-%d %H:%M:%S')
        else:
            de = date_end
        return '%sT%s/%sT%s' % (
            ds.strftime('%Y-%m-%d'),
            ds.strftime('%H:%M'),
            de.strftime('%Y-%m-%d'),
            de.strftime('%H:%M'),
        )

    def generate_feed(self):
        env = request.env
        url = '/google-shopping.xml'
        website = request.website
        ir_attachment = env['ir.attachment']
        attachment = ir_attachment.sudo().search([
            ('name', '=', url),
            ('type', '=', 'binary'),
        ], limit=1)
        content = None
        if attachment:
            expiry_hours = website.google_feed_expiry_time
            expiry_delta = timedelta(hours=expiry_hours)
            if fields.Datetime.now() - attachment.create_date < expiry_delta:
                try:
                    content = base64.b64decode(attachment.datas).decode(
                        'utf-8')
                except Exception:
                    content = None
        if not content:
            if attachment:
                attachment.sudo().unlink()
            xml_id = 'website_sale_google_shopping.rss'
            domain = [
                '|',
                ('website_id', '=', website.id),
                ('website_id', '=', False),
                ('sale_ok', '=', True),
                ('website_published', '=', True),
                '|', ('company_id', '=', website.company_id.id),
                ('company_id', '=', False),
            ]
            limit = website.google_feed_size or None
            products = env['product.template'].sudo().search(
                domain, limit=limit
            )
            pricelist = website.pricelist_id
            currency = pricelist.currency_id
            values = {
                'products': products,
                'currency': currency,
                'website': website,
                'url_root': website.domain,
                'updated': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                'get_effective_date': partial(self.get_effective_date),
            }
            content = env['ir.qweb']._render(xml_id, values)
            if content:
                if isinstance(content, bytes):
                    content = content.decode('utf-8')
                content = content.strip()
                content = re.sub(r' data-oe-[a-zA-Z\-]+="[^"]*"', '', content)
                content = content.replace('__colon__', ':')
                content = content.replace('<links>', '<link>')
                content = content.replace('</links>', '</link>')
                encoded_content = base64.b64encode(content.encode('utf-8'))
                ir_attachment.sudo().create({
                    'name': url,
                    'type': 'binary',
                    'datas': encoded_content,
                    'mimetype': FEED_MIMETYPE,
                    'public': True,
                })
        return content

    @http.route('/google-shopping.xml', type='http', auth='public', website=True)
    def feed_rss(self, **post):
        content = self.generate_feed()
        return request.make_response(
            content,
            headers=[('Content-Type', FEED_MIMETYPE)]
        )
