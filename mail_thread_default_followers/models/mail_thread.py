##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################
from odoo import models


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def _custom_mail_follower_options(self, res, followers_setting, email_from):
        def _add_mail_custom_follower(self, res, partner):
            self.env['mail.followers'].create({
                'res_model': res._name,
                'res_id': res.id,
                'partner_id': partner.id,
            })
        mail_partner = email_from and self.env['res.partner'].search([
            ('email', '=', email_from),
        ], limit=1) or False
        if mail_partner:
            _add_mail_custom_follower(res, mail_partner)
        _add_mail_custom_follower(res, res.create_uid)
        if followers_setting == 'owner_writers':
            for user in self.write_uid:
                _add_mail_custom_follower(res, user)
            return
        elif followers_setting == 'owner_partner' and res.partner_id:
            _add_mail_custom_follower(res, res.partner_id)

    def create(self, vals_list):
        model = self.env['ir.model'].search([('model', '=', self._name)])
        if model.followers_setting == 'default':
            return super().create(vals_list)
        ctx = {'tracking_disable': True}
        res = super(MailThread, self.with_context(ctx)).create(vals_list)
        if model.followers_setting == 'none':
            return res
        email_from = vals_list['email_from'] or False
        self._custom_mail_follower_options(
            res, model.followers_setting, email_from)
        return res
