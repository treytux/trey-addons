# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, api, _, exceptions


class ProjectTask(models.Model):
    _inherit = 'project.task'

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id and self.partner_id.task_warn != 'no-message':
            title = _('Warning for %s') % self.partner_id.name
            message = self.partner_id.task_warn_msg or ''
            if self.partner_id.task_warn == 'block':
                raise exceptions.Warning(title, message)
            return {'warning': {'title': title, 'message': message}}
