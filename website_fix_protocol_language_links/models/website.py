###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models
from odoo.http import request


class Website(models.Model):
    _inherit = 'website'

    @api.multi
    def get_alternate_languages(self, req=None):
        req = request.httprequest if not req else req
        if request.website:
            protocol = request.website.get_canonical_url().split('://')[0]
            if protocol in ['http', 'https']:
                req.url_root = '%s://%s' % (
                    protocol, req.url_root.split('://')[1])
        return super(Website, self).get_alternate_languages(req)
