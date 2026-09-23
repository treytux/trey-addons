###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id and self.partner_id.task_warn != 'no-message':
            title = _('Warning for %s') % self.partner_id.name
            message = self.partner_id.task_warn_msg or ''
            if self.partner_id.task_warn == 'block':
                raise exceptions.UserError(message)
            return {'warning': {'title': title, 'message': message}}
