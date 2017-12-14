# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api
import logging
_log = logging.getLogger(__name__)


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    @api.model
    def _search_suitable_rule(self, procurement, domain):
        '''Inherit function to avoid applying pull rules when 'no_apply_rules'
        is in the context.'''
        if ('no_apply_rules' in self.env.context and
                self.env.context['no_apply_rules'] is True):
            return []
        return super(ProcurementOrder, self)._search_suitable_rule(
            procurement, domain)
