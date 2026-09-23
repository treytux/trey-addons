###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo import _, models
from odoo.exceptions import UserError
from odoo.tools import html2plaintext

_logger = logging.getLogger(__name__)


class ProjectTask(models.Model):
    _inherit = 'project.task'

    def _get_task_context_for_chatgpt(self):
        self.ensure_one()
        context_parts = []
        context_parts.append(_('Task Title: %s\n') % self.name)
        if self.description:
            description_text = html2plaintext(self.description).strip()
            if description_text:
                context_parts.append(_(
                    'Task Description:\n%s\n') % description_text)
            else:
                context_parts.append(_(
                    'Task Description: (No description provided or '
                    'description is empty after HTML cleanup)\n'))
        else:
            context_parts.append(_(
                'Task Description: (No description provided)\n'))
        messages = self.env['mail.message'].search([
            ('model', '=', 'project.task'),
            ('res_id', '=', self.id),
            ('message_type', 'in', ['comment', 'email', 'notification']),
            ('body', '!=', False),
            ('body', '!=', '<p><br></p>'),
        ], order='date asc')
        if messages:
            conversation_history = ['\n' + _(
                'Conversation History (oldest to newest):')]
            for msg in messages:
                body_text = html2plaintext(msg.body).strip()
                if body_text:
                    conversation_history.append(
                        '- {author_name} ({msg_date_formatted}): {body_text}')

            if len(conversation_history) > 1:
                context_parts.append('\n'.join(conversation_history))
        else:
            context_parts.append('\n' + _(
                'Conversation History: (No relevant messages yet)'))
        return '\n'.join(context_parts)

    def action_solve_with_chatgpt(self):
        if len(self.ids) > 1:
            raise UserError(_(
                'Please select only one task at a time to request a ChatGPT solution.'))
        task = self
        task.ensure_one()
        _logger.info(_(
            'Requesting ChatGPT solution for task: %s (ID: %s)'),
            task.name, task.id)
        try:
            task_context = task._get_task_context_for_chatgpt()
            prompt_for_chatgpt = (_(
                'Based on the following Odoo task information (Title, '
                'Description, and Conversation History), please provide a '
                'concise and actionable solution or suggest the next steps to '
                'resolve it. Focus on practical steps, and if applicable, '
                'mention specific Odoo configurations or actions.\n\n'
                '--- Task Details and Conversation ---\n'
                '%s\n'
                '--- End of Task Details and Conversation ---\n\n'
                'Proposed solution or next steps (be specific and '
                'actionable):') % task_context
            )
            _logger.debug(
                'Prompt for ChatGPT for task %s:\n%s',
                task.id, prompt_for_chatgpt)
            connector = self.env['chatgpt.api.connector']
            solution_proposal = connector.chat_completion(
                prompt=prompt_for_chatgpt)
            _logger.info(_(
                'ChatGPT proposed solution for task %s:\n%s'),
                task.id, solution_proposal)
            if solution_proposal:
                solution_html = solution_proposal.replace('\n', '<br/>')
                message_body = (_(
                    '<strong>ChatGPT Solution Proposal:</strong><br/>%s') %
                    solution_html)
                task.message_post(
                    body=message_body,
                    message_type='comment',
                    subtype_xmlid='mail.mt_note'
                )
                _logger.info(_(
                    'Solution posted as internal note for task %s'), task.id)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('ChatGPT Solution'),
                        'message': _(
                            'Solution proposed by ChatGPT has been added to '
                            'the chatter as an internal note.'),
                        'sticky': False,
                        'type': 'success',
                    }
                }
            else:
                _logger.warning(_(
                    'ChatGPT returned an empty solution for task %s.'),
                    task.id)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('ChatGPT Solution'),
                        'message': _(
                            'ChatGPT returned an empty solution. You might '
                            'want to try again or rephrase the task details.'),
                        'sticky': True,
                        'type': 'warning',
                    }
                }
        except UserError as ue:
            _logger.error(_(
                'UserError while getting ChatGPT solution for task %s: %s'),
                task.id, str(ue))
            raise
        except Exception as e:
            _logger.error(_(
                'Unexpected error while getting ChatGPT solution for '
                'task %s: %s'), task.id, str(e), exc_info=True)
            raise UserError(_(
                'An unexpected error occurred while contacting ChatGPT or '
                'processing its response for task "%s": %s') % (
                    task.name, str(e))
            )
        return True
