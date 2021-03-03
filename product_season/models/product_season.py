###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductSeason(models.Model):
    _name = 'product.season'
    _description = 'Product season'
    _order = 'name'

    name = fields.Char(
        string='Name',
        translate=True,
        required=True)
    company_id = fields.Many2one(
        string='Company',
        comodel_name='res.company',
        required=True,
        default=lambda self: self.env.user.company_id.id)
    date_from = fields.Date(
        string='From')
    date_to = fields.Date(
        srtring='To')
    product_tmpl_ids = fields.One2many(
        string='Products',
        comodel_name='product.template',
        inverse_name='season_id')
    product_tmpl_count = fields.Integer(
        string='Products count',
        compute='_compute_products_count')

    @api.multi
    @api.depends('product_tmpl_ids')
    def _compute_products_count(self):
        for season in self:
            season.product_tmpl_count = len(self.product_tmpl_ids)
