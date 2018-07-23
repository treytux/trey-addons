# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    ecommerce_agent = fields.Boolean(
        compute='_ecommerce_agent',
        string='Ecommerce agent')

    @api.one
    def _ecommerce_agent(self):
        self.ecommerce_agent = self.has_group(
            'website_sale_season_by_user.group_ecommerce_agent')
