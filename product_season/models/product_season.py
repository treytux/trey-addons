# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class ProductSeason(models.Model):
    _name = 'product.season'
    _description = 'Product season'

    name = fields.Char(
        string='Name',
        size=255,
        translate=True,
        required=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id.id)
    date_from = fields.Date(
        string='From')
    date_to = fields.Date(
        srtring='To')
    product_tmpl_ids = fields.One2many(
        comodel_name='product.template',
        inverse_name='season_id',
        string='Products')
    product_tmpl_count = fields.Integer(
        string='Products count',
        compute='_compute_products_count')

    @api.one
    @api.depends('product_tmpl_ids')
    def _compute_products_count(self):
        self.product_tmpl_count = len(self.product_tmpl_ids)
