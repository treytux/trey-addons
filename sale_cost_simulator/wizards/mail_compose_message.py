###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models
from odoo.exceptions import ValidationError


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    def send_mail(self, auto_commit=False):
        ctx = self.env.context
        if ctx.get('default_model') != 'sale.cost.simulator':
            return super().send_mail(auto_commit=False)
        simulator_obj = self.env['sale.cost.simulator'].browse(
            ctx.get('active_id'))
        if not any([self.partner_ids, simulator_obj.partner_id]):
            raise ValidationError(_('Please, choose a partner.'))
        res = super().send_mail(auto_commit=False)
        simulator_obj.to_send()
        return res
