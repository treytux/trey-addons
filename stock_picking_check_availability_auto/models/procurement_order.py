# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    @api.multi
    def run(self, autocommit=False, context=None):
        this = self.with_context(auto_picking_assign=True)
        return super(ProcurementOrder, this).run(autocommit)
