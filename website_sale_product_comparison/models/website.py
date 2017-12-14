# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api, _
from openerp.exceptions import Warning

import logging
_log = logging.getLogger(__name__)


class Website(models.Model):
    _inherit = 'website'

    shop_products_per_comparison = fields.Integer(
        string=u'Products per Comparison',
        default=3
    )

    @api.one
    @api.constrains('shop_products_per_comparison')
    def _check_comparison_limit(self):
        if self.shop_products_per_comparison <= 0:
            raise Warning(
                _('Products per comparison must be greater than ''zero.')
            )
