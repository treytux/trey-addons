###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging
import re

from odoo import api, models

logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def _custom_mail_follower_options(self, res, followers_setting, email_from):
        def _add_mail_custom_follower(res, partners):
            for partner in partners:
                current_followers = self.env['mail.followers'].search([
                    ('res_model', '=', res._name),
                    ('res_id', '=', res.id),
                    ('partner_id', '=', partner.id),
                ])
                if not current_followers:
                    self.env['mail.followers'].create({
                        'res_model': res._name,
                        'res_id': res.id,
                        'partner_id': partner.id,
                    })
        partners_to_add = self.env['res.partner']
        mails = email_from and re.findall(
            r'[\w.+-]+@[\w-]+\.[\w.-]+', email_from) or []
        for mail in mails:
            partner = self.env['res.partner'].search([
                ('email', '=', mail),
            ], limit=1)
            if partner:
                partners_to_add += partner
        for record in res:
            if not mails and record.create_uid and record.create_uid.partner_id:
                partners_to_add += record.create_uid.partner_id
            if followers_setting == 'owner_writers':
                for user in self.write_uid:
                    if user.partner_id:
                        partners_to_add += user.partner_id
            elif (followers_setting == 'owner_partner'
                    and record.get('partner_id')):
                partners_to_add += record.partner_id
            _add_mail_custom_follower(record, partners_to_add)

    @api.model
    def create(self, vals_list):
        model = self.env['ir.model'].search([('model', '=', self._name)])
        if model.followers_setting == 'default':
            return super().create(vals_list)
        if not isinstance(vals_list, (list, dict)):
            logger.warn('Invalid values in create method of %s' % self._name)
            return super().create(vals_list)
        self = self.with_context({'mail_create_nosubscribe': True})
        if self._name == 'project.task':
            if isinstance(vals_list, list):
                for vals in vals_list:
                    if not vals.get('user_id'):
                        vals['user_id'] = False
            elif isinstance(vals_list, dict):
                if not vals_list.get('user_id'):
                    vals_list['user_id'] = False
        res = super().create(vals_list)
        if model.followers_setting == 'none':
            return res
        if isinstance(vals_list, list):
            for vals in vals_list:
                email_from = vals.get('email_from', False)
                self._custom_mail_follower_options(
                    res, model.followers_setting, email_from)
        elif isinstance(vals_list, dict):
            email_from = vals_list.get('email_from', False)
            self._custom_mail_follower_options(
                res, model.followers_setting, email_from)
        return res
