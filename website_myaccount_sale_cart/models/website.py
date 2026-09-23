# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class Website(models.Model):
    _inherit = 'website'

    @api.model
    def sale_get_order(self, force_create=False, code=None,
                       update_pricelist=None, context=None):
        res = super(Website, self).sale_get_order(
            force_create, code, update_pricelist)
        if res and not res.website_order:
            res.website_order = True
        return res
