###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from openerp import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    agreements_count = fields.Integer(
        string='Agreements count',
        compute='_compute_agreements_count',
    )
    agreements_unaccepted = fields.Integer(
        string='Agreements unaccepted',
        compute='_compute_agreements_unaccepted',
        store=False,
    )

    @api.multi
    def _compute_agreements_count(self):
        for partner in self:
            agreements = self.env['agreement.acceptance'].search([
                ('partner_id', '=', partner.id),
            ])
            partner.agreements_count = len(agreements)

    @api.multi
    def _compute_agreements_unaccepted(self):
        for partner in self:
            agreements = self.env['agreement.acceptance'].search_count([
                ('partner_id', '=', partner.id),
                ('state', '=', 'unaccepted')])
            partner.agreements_unaccepted = agreements
