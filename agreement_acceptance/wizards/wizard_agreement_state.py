###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, exceptions, fields, models


class WizardAgreementState(models.TransientModel):
    _name = 'wizard.agreement.state'
    _description = 'Wizard to change the agreement state'

    @api.model
    def _get_domain_partner_id(self):
        agreement_id = self.env['agreement.acceptance'].browse(
            self.env.context.get('active_id', None))
        partner_id = agreement_id.partner_id
        return [("is_company", "=", False), ("parent_id", "=", partner_id.id)]

    acceptance_date = fields.Date(
        string='Acceptance Date',
        default=fields.Date.today(),
    )
    acceptance_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Acceptance contact',
        domain=_get_domain_partner_id,
    )

    def check_partners(self, active_ids):
        agreements = self.env['agreement.acceptance'].browse(
            active_ids)
        partner_id = agreements[0].partner_id
        partners_count = self.env['agreement.acceptance'].search_count([
            ('id', 'in', active_ids),
            ('partner_id', '=', partner_id.id),
        ])
        if partners_count != len(active_ids):
            raise exceptions.UserError(
                ('All agreements need to have the same partner'))
        return

    @api.one
    def button_accept(self, data):
        self.ensure_one()
        self.check_partners(data['active_ids'])
        for agreement in self.env['agreement.acceptance'].browse(
                data['active_ids']):
            if agreement.state == 'unaccepted':
                agreement.state = 'accepted'
                agreement.acceptance_date = self.acceptance_date
                agreement.acceptance_partner_id = self.acceptance_partner_id
