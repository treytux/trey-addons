###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    sepa_direct_debit_legal_text = fields.Html(
        string='SEPA Direct Debit Legal Text',
        translate=True,
        sanitize=True,
    )
