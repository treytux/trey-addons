###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    sepa_creditor_identifier = fields.Char(
        string='SEPA Creditor Identifier', size=35)
    initiating_party_issuer = fields.Char(
        string='Initiating Party Issuer', size=35)
    initiating_party_identifier = fields.Char(
        string='Initiating Party Identifier', size=35)
    initiating_party_scheme = fields.Char(
        string='Initiating Party Scheme', size=35)
