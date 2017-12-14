# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models, _


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def _create_welcome_message(self, user):
        if not self.has_group('base.group_user'):
            return False
        selected_body = self.env.ref(
            'email_custom_formats.welcome_msg').body_html
        subject = _('Welcome')
        return user.partner_id.message_post(
            body=selected_body, subject=subject)
