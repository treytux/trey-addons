# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    partner_categs_name = fields.Char(
        string='Partner categories',
        compute='_compute_partner_categs_name',
        store=True)

    @api.one
    @api.depends('partner_id.category_id')
    def _compute_partner_categs_name(self):
        self.partner_categs_name = ', '.join(list(set([
            categ.name for categ in self.partner_id.category_id])))
