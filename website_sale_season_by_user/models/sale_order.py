# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class website(models.Model):
    _inherit = 'website'

    @api.multi
    def sale_product_domain(self):
        r = super(website, self).sale_product_domain()
        is_ecommerce_agent = self.env['res.users'].has_group(
            'website_sale_season_by_user.group_ecommerce_agent')
        if is_ecommerce_agent:
            r += [
                '|', ('season_id.agent', '=', True),
                ('season_id.public', '=', True)]
        else:
            r += [('season_id.public', '=', True)]
        return r
