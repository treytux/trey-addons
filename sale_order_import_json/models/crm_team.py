###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    import_payment_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Payment journal when import JSON',
    )
