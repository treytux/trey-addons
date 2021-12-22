###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    simplified_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Simplified invoice journal',
        required=True,
    )
