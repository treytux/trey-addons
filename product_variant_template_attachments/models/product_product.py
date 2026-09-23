###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _compute_message_attachment_count(self):
        attachment_obj = self.env['ir.attachment']
        for product in self:
            domain = [
                '|', '&',
                ('res_id', '=', product.product_tmpl_id.id),
                ('res_model', '=', 'product.template'),
                '&',
                ('res_id', '=', product.id),
                ('res_model', '=', 'product.product'),
            ]
            product.message_attachment_count = attachment_obj.search_count(
                domain)
