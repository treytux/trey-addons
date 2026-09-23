###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import ast
import base64
import json

from odoo import _, exceptions, fields, models


class AccountMoveImportFile(models.TransientModel):
    _name = 'account.move.import_file'
    _description = 'Wizard to import file for create account moves'

    file = fields.Binary(
        string='File',
        required=True,
    )
    filename = fields.Char(
        string='Filename',
    )
    type = fields.Selection(
        selection=[
        ],
        string='Type',
        required=True,
        default=None,
    )

    def get_file_content(self):
        self.ensure_one()
        file_content = base64.b64decode(self.file)
        for decode in ('utf-8', 'iso8859-1', 'latin-1'):
            try:
                return file_content.decode(decode)
            except UnicodeDecodeError:
                pass
        raise exceptions.UserError(
            _('The file could not be decoded, please try with another file.'))

    def import_file(self):
        self.ensure_one()
        moves = self._import_file()
        action = self.env.ref('account.action_move_journal_line').read()[0]
        action['domain'] = [('id', 'in', moves.ids)]
        ctx = action.get('context', '{}')
        if isinstance(ctx, str):
            try:
                ctx = json.loads(ctx)
            except json.JSONDecodeError:
                ctx = ast.literal_eval(ctx)
        action['context'] = {
            k: v for k, v in ctx.items()
            if k != 'search_default_posted'
        } if isinstance(ctx, dict) else {}
        return action

    def _import_file(self):
        self.ensure_one()
        method = f'_import_file_{self.type or "none"}'
        if not hasattr(self, method):
            raise NotImplementedError(
                f'This method {method} must be implemented.')
        journal = self.env[self._context['active_model']].browse(
            self._context['active_ids'][0])
        return getattr(self, method)(journal, self.get_file_content())

    def _import_file_none(self, journal, content):
        raise exceptions.UserError(
            _('The type of file to import has not been defined.'))
