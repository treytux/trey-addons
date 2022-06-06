###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    asin = fields.Char(
        string='Amazon Standard Identification Number',
        copy=False,
    )

    @api.constrains('asin')
    def _check_asin(self):
        for template in self:
            if not template.asin:
                continue
            found = template.search([
                ('id', '!=', template.id),
                ('asin', '=', template.asin),
            ])
            if not found:
                continue
            raise exceptions.ValidationError(
                _('ASIN "%s" already exists for product "%s"') % (
                    template.asin, found[0].name))
