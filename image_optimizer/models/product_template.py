###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = ['product.template', 'image.optimizer']

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if res.image:
            res.optimize_images(res.image)
        return res

    def write(self, vals):
        res = super().write(vals)
        if vals.get('image', False):
            self.optimize_images(self.image)
        return res
