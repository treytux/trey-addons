###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    google_title = fields.Char(
        string='Google Title',
        compute='_compute_google_title',
    )

    @api.one
    @api.depends('name', 'attribute_value_ids')
    def _compute_google_title(self):
        google_title = self.name
        var_title = [
            '%s %s' % (a.attribute_id.name, a.name) for a in
            self.attribute_value_ids]
        self.google_title = '%s%s' % (
            google_title,
            var_title and ' - %s' % ' '.join(var_title) or '',
        )
