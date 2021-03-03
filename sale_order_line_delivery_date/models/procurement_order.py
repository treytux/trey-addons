# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    @api.model
    def _run_move_create(self, procurement):
        res = super(ProcurementOrder, self)._run_move_create(procurement)
        proc = self.env['procurement.order'].browse(res['procurement_id'])
        if not proc.sale_line_id:
            return res
        forced_date = proc.sale_line_id.initial_delivery_date
        res.update({
            'date_expected': forced_date,
        })
        return res
