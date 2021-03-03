###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class Website(models.Model):
    _inherit = 'website'

    protocol = fields.Char(
        string='Protocol',
        compute='_compute_protocol',
    )

    @api.depends('canonical_domain', 'domain')
    def _compute_protocol(self):
        for website in self:
            website.protocol = website.get_canonical_url().split('://')[0]
