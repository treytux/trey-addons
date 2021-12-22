###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    is_private_shop = fields.Boolean(
        string='Is private shop',
    )

    def get_is_private_shop(self):
        return self.is_private_shop
