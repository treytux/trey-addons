# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, api, exceptions, _
import logging
_log = logging.getLogger(__name__)


class ProjectIssue(models.Model):
    _inherit = 'project.issue'

    @api.multi
    def onchange_partner_id(self, partner_id):
        if not partner_id:
            return {}

        def _message_parent(partner):
            if partner and partner.issue_warn != 'no-message':
                title = _('Warning for %s') % partner.name
                message = partner.task_warn_msg or ''
                if partner.task_warn == 'block':
                    raise exceptions.Warning(title, message)
                return {'warning': {'title': title, 'message': message}}
            if partner.parent_id:
                return _message_parent(partner.parent_id)
            return {}

        contact = self.env['res.partner'].browse(partner_id)
        return _message_parent(contact)
