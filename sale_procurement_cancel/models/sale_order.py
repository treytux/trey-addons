# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_cancel(self):
        if not self.procurement_group_id:
            return super(SaleOrder, self).action_cancel()
        procurements = self.env['procurement.order'].search([
            ('group_id', '=', self.procurement_group_id.id),
            ('state', '!=', 'done')])
        proc_init_states = {}
        for proc in procurements:
            if proc.rule_id.action == 'buy' and proc.purchase_line_id:
                if proc.purchase_line_id.state == 'draft':
                    proc.purchase_line_id.action_cancel()
                if proc.purchase_line_id.state not in ('draft', 'cancel'):
                    proc_init_states[proc.id] = proc.state
                    proc.state = 'done'
        res = super(SaleOrder, self).action_cancel()
        for proc in procurements:
            if proc_init_states.get(proc.id):
                proc.state = proc_init_states[proc.id]
        return res
