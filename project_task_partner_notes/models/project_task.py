###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'project.task'

    partner_comment = fields.Text(
        string='Partner internal notes',
        related='partner_id.commercial_partner_id.comment',
        readonly=True,
    )
