###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api
from odoo.addons.payment_redsys.models import redsys


class AcquirerRedsys(redsys.AcquirerRedsys):
    @api.model
    def _get_website_url(self):
        res = super()._get_website_url()
        website_id = self.env.context.get('website_id', False)
        if website_id:
            website = self.env['website'].browse(website_id)
            protocol = website.get_canonical_url().split(':')[0]
            if protocol in ['http', 'https']:
                return '%s://%s' % (protocol, website.domain)
        return res
