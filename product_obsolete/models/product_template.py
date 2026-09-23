###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_obsolete = fields.Boolean(
        string='Is obsolete',
        compute='_compute_is_obsolete',
        store=True,
        inverse='_inverse_is_obsolete',
    )

    @api.depends('product_variant_ids.is_obsolete')
    def _compute_is_obsolete(self):
        for product_tmpl in self:
            product_tmpl.is_obsolete = all(
                product_tmpl.product_variant_ids.mapped('is_obsolete'))

    @api.multi
    def _inverse_is_obsolete(self):
        for product_tmpl in self:
            for product in product_tmpl.product_variant_ids:
                product.is_obsolete = product_tmpl.is_obsolete
