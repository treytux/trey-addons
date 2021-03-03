###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def copy(self, default=None):
        self.ensure_one()
        res = super().copy(default=default)
        if not self.seller_ids:
            return res
        res.seller_ids.create({
            'product_tmpl_id': res.id,
            'name': self.seller_ids[0].name.id,
        })
        return res
