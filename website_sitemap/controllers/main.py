# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import openerp
from openerp.addons.web import http
from openerp.addons.website.controllers import main
from openerp.http import request
from itertools import islice
import datetime


class Website(main.Website):

    @http.route()
    def sitemap_xml_index(self):
        # Original function is replaced because it's imposible to change
        # url_root without overriding it. Also, we filter results using
        # 'urls_to_exclude' config parameter.
        env = request.env
        ira = env['ir.attachment']
        icp = env['ir.config_parameter']
        mimetype = 'application/xml;charset=utf-8'
        content = None

        def create_sitemap(url, content):
            ira.sudo().create(dict(
                datas=content.encode('base64'),
                mimetype=mimetype,
                type='binary',
                name=url,
                url=url))
        sitemap = ira.sudo().search_read([(
            'url', '=', '/sitemap.xml'),
            ('type', '=', 'binary')],
            ('datas', 'create_date'))
        if sitemap:
            server_format = openerp.tools.misc.DEFAULT_SERVER_DATETIME_FORMAT
            create_date = datetime.datetime.strptime(
                sitemap[0]['create_date'], server_format)
            delta = datetime.datetime.now() - create_date
            if delta < datetime.timedelta(
                    hours=request.website.expiry_time):
                content = sitemap[0]['datas'].decode('base64')
        if not content:
            sitemap_ids = ira.sudo().search([
                ('url', '=like', '/sitemap%.xml'),
                ('type', '=', 'binary')])
            if sitemap_ids:
                sitemap_ids.sudo().unlink()
            pages = 0
            first_page = None
            locs = request.website.sudo(
                user=request.website.user_id.id).custom_enumerate_pages()
            base_url = icp.get_param('web.base.url')
            temp_sitemap_locs = env.ref('website.sitemap_locs')
            temp_sitemap_xml = env.ref('website.sitemap_xml')
            while True:
                values = {
                    'locs': islice(locs, 0, main.LOC_PER_SITEMAP),
                    'url_root': base_url or request.httprequest.url_root[:-1],
                }
                urls = temp_sitemap_locs.render(values)
                if urls.strip():
                    page = temp_sitemap_xml.render(dict(content=urls))
                    if not first_page:
                        first_page = page
                    pages += 1
                    create_sitemap('/sitemap-%d.xml' % pages, page)
                else:
                    break
            if not pages:
                return request.not_found()
            elif pages == 1:
                content = first_page
            else:
                temp_sitemap_index_xml = env.ref('website.sitemap_index_xml')
                content = temp_sitemap_index_xml.render(dict(
                    pages=range(1, pages + 1),
                    url_root=request.httprequest.url_root))
            create_sitemap('/sitemap.xml', content)
        return request.make_response(content, [('Content-Type', mimetype)])
