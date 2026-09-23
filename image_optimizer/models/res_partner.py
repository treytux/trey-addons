###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'image.optimizer']

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if self.image:
            res.optimize_images(self.image)
        return res

    def write(self, vals):
        res = super().write(vals)
        if vals.get('image', False):
            self.optimize_images(self.image)
        return res
