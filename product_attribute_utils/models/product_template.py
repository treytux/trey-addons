###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def _has_attribute(self, attribute_id):
        self.ensure_one()
        return any([
            li.attribute_id.id for li in self.attribute_line_ids
            if attribute_id == li.attribute_id.id])

    @api.multi
    def _get_color_attribute(self):
        self.ensure_one()
        attrs = [
            line.attribute_id for line in self.attribute_line_ids if
            line.attribute_id.type == 'color']
        return attrs and attrs[0] or False
