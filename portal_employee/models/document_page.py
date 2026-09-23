###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo import _, api, models

_logger = logging.getLogger(__name__)


class DocumentPage(models.Model):
    _inherit = 'document.page'

    @api.multi
    def action_notify_new_document(self):
        for page in self:
            if page.parent_id:
                users = page.env['res.users'].search([
                    '|',
                    ('knowledge_categories', 'in', [page.parent_id.id]),
                    ('knowledge_categories.child_ids', 'in', [
                        page.parent_id.id]),
                ])
                template = page.env.ref('portal_employee.notify_new_document')
                if not template:
                    _logger.info(
                        'Cannot notify new document: template '
                        '"portal_employee.notify_new_document" not exists.')
                else:
                    template_values = {
                        'email_to': False,
                        'email_cc': False,
                        'auto_delete': True,
                        'partner_to': False,
                        'scheduled_date': False,
                    }
                    template.write(template_values)
                    for user in users:
                        if not user.email:
                            _logger.info(
                                'Cannot notify new document: user %s has no'
                                ' email address.', user.name)
                        else:
                            template_values['email_to'] = user.email
                            template.write(template_values)
                            with page.env.cr.savepoint():
                                template.with_context(
                                    lang=user.lang).send_mail(
                                    page.id, force_send=True,
                                    raise_exception=False)
                    body_msg = _('New document notified to users: %s')
                    page.message_post(
                        body=body_msg % (', '.join(users.filtered(
                            lambda user: user.email).mapped('name'))),
                        message_type='email',
                        subtype='mail.mt_note'
                    )
