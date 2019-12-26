# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, _
import logging
_log = logging.getLogger(__name__)


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    @api.multi
    def get_proc_exception_domain(self):
        return [
            ('state', '=', 'exception'),
        ]

    @api.multi
    def get_proc_exception_order(self):
        return 'company_id asc, id asc'

    @api.model
    def procurement_send_exception_errors(self):
        def _get_user2to_inform_by_company(self):
            to_inform = []
            stock_conf = self.env['stock.config.settings'].get_default_values(
                'users_to_send_exception_ids')
            users_to_send_exception_ids = (
                len(stock_conf['users_to_send_exception_ids']) and
                stock_conf['users_to_send_exception_ids'][0] and
                stock_conf['users_to_send_exception_ids'][0][2] or [])
            if not users_to_send_exception_ids:
                _log.warning(_(
                    'No user was found in the field \'Users who will be '
                    'informed by mail of procurement in exception state\'. '
                    'To receive emails you must add at least one from the '
                    'Configuration/Configuration/Warehouse menu!'))
                return []
            to_inform += [
                user for user in
                self.env['res.users'].browse(users_to_send_exception_ids)]
            return list(set(to_inform))

        procs_exception = self.search(
            self.get_proc_exception_domain(),
            order=self.get_proc_exception_order())
        if not procs_exception:
            return False
        body_html = '''
            <div style="font-family: 'Lucida Grande', Ubuntu, Arial, Verdana,
            sans-serif; font-size: 12px; color: rgb(34, 34, 34);
            background-color: #FFF; ">
                <h3>%s </h3>
                <ul>
        ''' % _('Procurement orders in exception state to review:')
        currenty_company_name = ''
        for proc_exception in procs_exception:
            if currenty_company_name != proc_exception.company_id.name:
                currenty_company_name = proc_exception.company_id.name
                body_html += '<p>%s %s:</p>' % (
                    _('Company'), _(currenty_company_name))
            body_html += _('''
                <li>Procurement Id = %s with source document: \'%s\'.</li>
            ''') % (proc_exception.id, proc_exception.origin)
        body_html += '''
            </ul>
            <br><br>
        '''
        users2inform = _get_user2to_inform_by_company(self)
        if not users2inform:
            return False
        mail = self.env['mail.mail'].create({
            'email_from': self.env.user.partner_id.email,
            'recipient_ids': [(6, 0, [u.partner_id.id for u in users2inform])],
            'subject': _('Procurements in exception'),
            'body_html': body_html,
            'state': 'outgoing',
            'type': 'email',
        })
        mail.send()
