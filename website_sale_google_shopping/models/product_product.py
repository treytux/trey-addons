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

    @api.depends('name', 'product_template_variant_value_ids')
    def _compute_google_title(self):
        for record in self:
            google_title = record.name
            var_title = [
                '%s %s' % (ptav.attribute_id.name, ptav.name)
                for ptav in record.product_template_variant_value_ids
            ]
            record.google_title = '%s%s' % (
                google_title,
                var_title and ' - %s' % ' '.join(var_title) or '',
            )

    def _get_google_feed_identifier(self):
        self.ensure_one()
        template = self.product_tmpl_id
        if template.product_variant_count > 1:
            return self.default_code or str(self.id)
        return template.default_code or self.default_code or str(self.id)
