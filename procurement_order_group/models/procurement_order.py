# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    season_id = fields.Many2one(
        comodel_name='product.season',
        compute='_compute_season',
        store=True,
        string='Season')
    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        compute='_compute_product_tmpl',
        store=True,
        string='Product template')
    categ_id = fields.Many2one(
        comodel_name='product.category',
        compute='_compute_product_categ',
        store=True,
        string='Category')

    @api.multi
    @api.depends('product_id')
    def _compute_season(self):
        for procurement in self:
            procurement.season_id = (
                procurement.product_id.season_id and
                procurement.product_id.season_id.id or None)

    @api.multi
    @api.depends('product_id')
    def _compute_product_tmpl(self):
        for procurement in self:
            procurement.product_tmpl_id = (
                procurement.product_id.product_tmpl_id and
                procurement.product_id.product_tmpl_id.id or None)

    @api.multi
    @api.depends('product_id')
    def _compute_product_categ(self):
        for procurement in self:
            procurement.categ_id = (
                procurement.product_id.categ_id and
                procurement.product_id.categ_id.id or None)
