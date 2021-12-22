###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ResPartnerZone(models.Model):
    _name = 'res.partner.zone'
    _description = 'Partner zone'

    name = fields.Char(
        string='Name',
    )
    partner_ids = fields.One2many(
        comodel_name='res.partner',
        inverse_name='zone_id',
        string='Partners',
    )
    partner_count = fields.Integer(
        string='Partners count',
        compute='_compute_partner_count',
    )

    @api.depends('partner_ids')
    def _compute_partner_count(self):
        for zone in self:
            zone.partner_count = len(zone.partner_ids)

    def action_view_partners(self):
        self.ensure_one()
        action = self.env.ref('contacts.action_contacts').read()[0]
        action['domain'] = [('id', 'in', self.partner_ids.ids)]
        return action
