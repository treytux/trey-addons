###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models, tools


class ProjectTask(models.Model):
    _inherit = 'project.task'

    @api.model
    def message_new(self, msg, custom_values=None):
        emails = tools.email_split(msg.get('from') or '')
        partner_ids = self._find_partner_from_emails(
            emails, force_create=False)
        self = self.with_context(only_subscribe_partner_ids=partner_ids)
        return super(ProjectTask, self).message_new(
            msg, custom_values=custom_values)

    @api.multi
    def message_subscribe(self, partner_ids=None, channel_ids=None,
                          subtype_ids=None):
        only_partner_ids = self._context.get('only_subscribe_partner_ids')
        if only_partner_ids:
            partner_ids = only_partner_ids
        return super().message_subscribe(
            partner_ids=partner_ids, channel_ids=channel_ids,
            subtype_ids=subtype_ids)
