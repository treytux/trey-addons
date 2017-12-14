# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    agents_name = fields.Char(
        string='Agents',
        compute='_compute_agents_name',
        store=True)

    @api.one
    @api.depends('order_line.agents')
    def _compute_agents_name(self):
        self.agents_name = ', '.join(list(set([
            ag.agent.name for line in self.order_line for ag in line.agents])))
