# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, api
import logging
import re
from urllib import urlencode
from urlparse import urljoin

_log = logging.getLogger(__name__)


class ProjectIssue(models.Model):
    _inherit = 'project.issue'

    @api.one
    def hangout_notify(self):
        def cleanhtml(raw_html):
            # raw_html = raw_html.replace('<br/>', '\n').replace('<br>', '\n')
            # raw_html = raw_html.replace('</p>', '\n').replace('<p/>', '\n')
            cleanr = re.compile('<.*?>')
            cleantext = re.sub(cleanr, '', raw_html)
            cleantext = cleantext.replace('\n', ' ').replace('\r', '')
            return cleantext.strip()

        # Componer la URL
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        query = {'db': self.env.cr.dbname}
        fragment = {
            'login': self.env.user.login,
            'action': 'mail.action_mail_redirect',
            'model': self._name,
            'res_id': self.id,
        }
        url = urljoin(base_url, "/web?%s#%s" % (urlencode(query), urlencode(
            fragment)))

        try:
            message = None
            for m in self.message_ids:
                if m.type == 'email':
                    if (message and m.date > message.date) or not message:
                        message = m
            if message:
                self.company_id.hangoutSendMessage('''(%s) %s\n%s\n%s''' % (
                    message.author_id.email,
                    url,
                    message.subject,
                    cleanhtml('%s' % message.body)[:200]))
        except Exception as e:
            _log.error('When notify issue to Hangout: %s' % e)
