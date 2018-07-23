# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    @api.onchange('partner_ids')
    def _onchange_partner_ids(self):
        def return_domain(partners):
            partner_list = []
            for partner in partners:
                partner_list += ([partner.id] + [
                    c.id for c in partner.child_ids if
                    c.model_name == self.env.context.get('active_model')])
            return {'domain': {'partner_ids': [('id', 'in', partner_list)]}}
        self.ensure_one()
        if self.partner_ids:
            return return_domain(self.partner_ids)
        model = self.env.context.get('active_model')
        if not model or 'partner_id' not in self.env[model]._fields.keys():
            return {'domain': {'partner_ids': []}}
        active_ids = self.env.context.get('active_ids')
        return return_domain(
            [self.env[model].search([('id', 'in', active_ids)]).partner_id])
