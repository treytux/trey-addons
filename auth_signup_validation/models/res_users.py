###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models, _
from odoo.exceptions import UserError
import logging
_log = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.one
    def action_activate_and_notify(self):
        template = self.env.ref(
            'auth_signup_validation.activation_notify_email')
        if not self.email:
            raise UserError(
                _('Cannot send email: user %s has no email address.')
                % self.name)
        self.partner_id.allowed = True
        template.with_context(lang=self.lang).send_mail(self.id)
        _log.info(
            'Activation notification email sent for user <%s> to <%s>',
            self.login, self.email)
