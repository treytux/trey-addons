# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, _
import logging
_log = logging.getLogger(__name__)


class IrCron(models.Model):
    _inherit = 'ir.cron'

    @api.model
    def cron_block_when_unpaid(self):
        def _get_user_to_inform_per_company(self):
            to_inform = []
            account_conf = self.env[
                'account.config.settings'].get_default_values(
                    'users_to_inform_ids')
            users_to_inform_ids = (
                len(account_conf['users_to_inform_ids']) and
                account_conf['users_to_inform_ids'][0] and
                account_conf['users_to_inform_ids'][0][2] or [])
            if not users_to_inform_ids:
                _log.warning(_(
                    'No user was found in the field \'Users whose will be '
                    'informed of their the blocked partners\'. '
                    'To receive emails you must add at least one from the '
                    'Configuration/Configuration/Accounting menu!'))
                return []
            to_inform += [
                user for user in
                self.env['res.users'].browse(users_to_inform_ids)]
            return list(set(to_inform))

        unpaid_partners = self.env['res.partner'].get_unpaid_partner()
        body_html = '''
            <div style="font-family: 'Lucida Grande', Ubuntu, Arial, Verdana,
            sans-serif; font-size: 12px; color: rgb(34, 34, 34);
            background-color: #FFF; ">
                <h3>%s </h3>
        ''' % _('Partners blocked:')
        body_html += ', <br/> '.join([(p.name) for p in unpaid_partners])
        users2inform = _get_user_to_inform_per_company(self)
        if not users2inform:
            return False
        mail = self.env['mail.mail'].create({
            'email_from': self.env.user.partner_id.email,
            'recipient_ids': [(6, 0, [u.partner_id.id for u in users2inform])],
            'subject': _('Partner blocked list'),
            'body_html': body_html,
            'state': 'outgoing',
            'type': 'email',
        })
        mail.send()
        return True
