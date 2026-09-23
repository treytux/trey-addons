###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models
from odoo.tools import email_split


class ProjectTask(models.Model):
    _inherit = 'project.task'

    def write(self, vals):
        before_followers = {
            task.id: set(task.message_partner_ids.ids) for task in self}
        res = super(ProjectTask, self).write(vals)
        if 'project_id' in vals:
            for task in self:
                after_followers = set(task.message_partner_ids.ids)
                newly_added = (
                    after_followers - before_followers.get(task.id, set()))
                assignee_partners = set(task.user_ids.mapped('partner_id').ids)
                to_remove = newly_added - assignee_partners
                if to_remove:
                    task.message_unsubscribe(partner_ids=list(to_remove))
        return res

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        if custom_values is None:
            custom_values = {}
        custom_values['user_ids'] = [(5, 0, 0)]
        create_context = dict(self.env.context or {})
        create_context['default_user_ids'] = False
        task = super(
            ProjectTask, self.with_context(create_context)
        ).message_new(msg_dict, custom_values)
        allowed_partner_ids = []
        author_id = msg_dict.get('author_id')
        if author_id:
            allowed_partner_ids.append(author_id)
        recipient_emails = msg_dict.get('to', '')
        if recipient_emails:
            recipient_addressses = email_split(recipient_emails)
            for email in recipient_addressses:
                partner = self.env['res.partner'].search(
                    [('email', '=', email)], limit=1)
                if partner:
                    allowed_partner_ids.append(partner.id)
        cc_emails = msg_dict.get('cc', '')
        if cc_emails:
            cc_addresses = email_split(cc_emails)
            for email in cc_addresses:
                partner = self.env['res.partner'].search(
                    [('email', '=', email)], limit=1)
                if partner:
                    allowed_partner_ids.append(partner.id)
        allowed_partner_ids = list(set(allowed_partner_ids))
        current_follower_ids = task.message_partner_ids.ids
        to_remove = [
            pid for pid in current_follower_ids
            if pid not in allowed_partner_ids
        ]
        if to_remove:
            task.message_unsubscribe(partner_ids=to_remove)
        if allowed_partner_ids:
            task.message_subscribe(partner_ids=allowed_partner_ids)
        return task
