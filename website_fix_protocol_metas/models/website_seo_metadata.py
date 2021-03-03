###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models
from odoo.http import request


class SeoMetadata(models.AbstractModel):
    _inherit = 'website.seo.metadata'

    def get_website_meta(self):
        metas = super().get_website_meta()
        if request.website.protocol not in ['http', 'https']:
            return metas
        for meta_key, meta_value in ([
                i for i in metas.items() if isinstance(i[1], str)]):
            for attr_key, attr_value in meta_value.items():
                if attr_value and attr_value.startswith('http://'):
                    metas[meta_key][attr_key] = '%s://%s' % (
                        request.website.protocol, attr_value.split('://')[1])
        return metas
