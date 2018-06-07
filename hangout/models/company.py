# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api, _
import logging
try:
    import xmpp
except ImportError:
    _log = logging.getLogger(__name__)
    _log.warning('You need install xmpp python module for use hangout addon')

_log = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    hangout_email = fields.Char(
        string='Email')
    hangout_password = fields.Char(
        string='Password',
        password=True)
    hangout_notify_accounts = fields.Char(
        string='Notify accounts',
        help='Accounts seperated by ;')

    @api.one
    def action_test_hangout(self):
        self.hangoutSendMessage(
            _('This messages is a test from Odoo %s') % self.env.cr.dbname)

    @api.one
    def hangoutSendMessage(self, message, accounts=None):
        company = self.env.user.company_id
        if accounts is None:
            accounts = company.hangout_notify_accounts
        accounts = accounts.split(';')
        try:
            jid = xmpp.protocol.JID(company.hangout_email)
            cl = xmpp.Client('gmail.com', debug=[])
            cl.connect()
            cl.auth(jid.getNode(), company.hangout_password)
            for account in accounts:
                cl.send(xmpp.protocol.Message(
                    account,
                    message, typ='chat'))
                _log.info('Sended Hangout message to %s' % account)
        except Exception as e:
            _log.error('Sending Hangout message from %s: %s' % (
                company.hangout_email, e))
        else:
            _log.info('Message "%s" sended to %s' % (
                message[:12], accounts))
