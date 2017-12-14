# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    visit_id = fields.Many2one(
        comodel_name='partner.visit',
        compute='_compute_visit_id',
        readonly=True,
        string='Visit')

    @api.one
    def _compute_visit_id(self):
        visits = self.env['partner.visit'].search([('order_id', '=', self.id)])
        self.visit_id = visits and visits[0].id or False
