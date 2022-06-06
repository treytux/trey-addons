###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    installation_product = fields.Boolean(
        string='Installation product',
    )
    product_tmpl_kit_id = fields.Many2one(
        comodel_name='product.template',
        string='Product kit',
        domain='[("pack_ok", "=", True)]',
    )

    @api.constrains('product_tmpl_kit_id')
    def _check_product_tmpl_kit_id(self):
        for product_tmpl in self:
            is_not_pack = (
                product_tmpl.installation_product
                and not product_tmpl.product_tmpl_kit_id.pack_ok)
            if is_not_pack:
                raise ValidationError(_(
                    'Warning! The \'Product kit\' field must be a pack.'))
