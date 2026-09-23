###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ResUsers(models.Model):
    _name = 'res.users'
    _inherit = ['res.users', 'image.optimizer']

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if res.image:
            self.optimize_images(res.image)
        return res

    def write(self, vals):
        res = super().write(vals)
        if vals.get('image', False):
            self.optimize_images(self.image)
        return res
