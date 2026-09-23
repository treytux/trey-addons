###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    invoice_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Invoice Journal',
        domain="[('type', '=', 'sale')]",
        help='Default invoice journal for orders from this sales team',
    )
