# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models
from openerp.addons.website.models import website
from openerp.addons.web.http import request
import logging
_log = logging.getLogger(__name__)


def url_for(path_or_uri, lang=None):
    url = website.url_for(path_or_uri, lang)

    if url in ('', '/', '/web'):
        return url

    if url.startswith('http'):
        return url

    for sw in ('/web/', '/web#', '/usr/', 'mailto', '#'):
        if url.startswith(sw):
            return url

    IrHttp = request.registry['ir.http']
    return IrHttp.url_for(url)


class UiView(models.Model):
    _name = "ir.ui.view"
    _inherit = "ir.ui.view"

    def render(self, cr, uid, id_or_xml_id, values=None, engine='ir.qweb',
               context=None):
        if values is None:
            values = {}
        values['url_for'] = url_for

        return super(UiView, self).render(cr, uid, id_or_xml_id, values,
                                          engine, context)
