###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class DiscountPartnerGroup(models.Model):
    _name = 'discount.partner.group'
    _description = 'Discount partner group'

    name = fields.Char(
        string='Group',
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company.id,
    )
    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        compute='_compute_partner_ids',
        inverse='_inverse_partner_ids',
        string='Partners',
    )

    @api.depends('company_id')
    def _compute_partner_ids(self):
        partner_model = self.env['res.partner'].with_context(active_test=False)
        for group in self:
            group.partner_ids = partner_model.search([
                ('dto_group_id', '=', group.id),
            ])

    def _inverse_partner_ids(self):
        partner_model = self.env['res.partner'].with_context(active_test=False)
        for group in self:
            current_partners = partner_model.search([
                ('dto_group_id', '=', group.id),
            ])
            removed_partners = current_partners - group.partner_ids
            added_partners = group.partner_ids - current_partners
            if removed_partners:
                removed_partners.write({
                    'dto_group_id': False,
                })
            if added_partners:
                added_partners.write({
                    'dto_group_id': group.id,
                })
