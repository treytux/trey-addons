###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class View(models.Model):
    _inherit = 'ir.ui.view'

    is_homepage = fields.Boolean(
        string='Homepage',
        related='first_page_id.is_homepage',
        readonly=False,
    )
    is_published = fields.Boolean(
        string='Published',
        related='first_page_id.is_published',
        readonly=False,
    )
