###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, exceptions, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_termoclub = fields.Boolean(
        string='Is TermoClub product',
        compute='_compute_is_termoclub',
    )

    @api.depends('seller_ids', 'seller_ids.name')
    def _compute_is_termoclub(self):
        supplier = self.env.user.company_id.termoclub_supplier_id
        for template in self:
            supplier_infos = template.seller_ids.filtered(
                lambda l: l.name == supplier)
            template.is_termoclub = bool(supplier_infos)

    @api.multi
    def action_termoclub_check_stock(self):
        self.ensure_one()
        if self.product_variant_count == 1:
            if not self.product_variant_id.is_termoclub:
                return
        message = self.product_variant_id.termoclub_check_stock()
        raise exceptions.UserError(message)
