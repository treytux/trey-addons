###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import ast

from lxml import etree
from odoo import _, api, models
from odoo.exceptions import AccessError


class BoardBoard(models.AbstractModel):
    _inherit = 'board.board'

    @api.model
    def _sanitize_board_action_context(self, context):
        if not context:
            return context
        try:
            context_dict = ast.literal_eval(context)
        except (SyntaxError, ValueError):
            return context
        if not isinstance(context_dict, dict):
            return context
        context_dict.pop('group_by', None)
        return repr(context_dict)

    @api.model
    def _sanitize_shared_snapshot_arch(self, archnode):
        for action_node in archnode.findall('.//action'):
            if action_node.get('context'):
                action_node.set(
                    'context',
                    self._sanitize_board_action_context(
                        action_node.get('context')
                    )
                )
        return archnode

    @api.model
    def _inject_board_attributes(self, arch, attributes):
        archnode = etree.fromstring(arch)
        board_node = archnode.find('.//board')
        if board_node is not None:
            for key, value in attributes.items():
                if value is None:
                    board_node.attrib.pop(key, None)
                else:
                    board_node.set(key, value)
        return etree.tostring(archnode, pretty_print=True, encoding='unicode')

    @api.model
    def _prepare_shared_snapshot_arch(self, arch, title):
        archnode = etree.fromstring(arch)
        archnode.set('string', title)
        archnode = self._sanitize_shared_snapshot_arch(archnode)
        board_node = archnode.find('.//board')
        if board_node is not None:
            board_node.attrib.pop('shareable', None)
            board_node.set('readonly', '1')
        return etree.tostring(archnode, pretty_print=True, encoding='unicode')

    @api.model
    def _get_shared_dashboard_from_view(self, view_id):
        if not view_id:
            return self.env['board.share.dashboard']
        return self.env['board.share.dashboard'].sudo().with_context(
            active_test=False
        ).search([('view_id', '=', view_id)], limit=1)

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        shared_dashboard = self._get_shared_dashboard_from_view(view_id)
        if shared_dashboard:
            user = self.env.user
            allowed = user == shared_dashboard.owner_id or (
                user in shared_dashboard.recipient_ids
            )
            if not shared_dashboard.active:
                raise AccessError(_('This shared dashboard is not available.'))
            if not allowed:
                raise AccessError(
                    _('You do not have access to this shared dashboard.')
                )
            res = super().get_view(
                view_id=view_id, view_type=view_type, **options)
            res.update({
                'custom_view_id': False,
                'arch': self._prepare_shared_snapshot_arch(
                    shared_dashboard.view_id.arch_db, shared_dashboard.name)
            })
            res['arch'] = self._arch_preprocessing(res['arch'])
            return res
        res = super().get_view(view_id=view_id, view_type=view_type, **options)
        if view_id == self.env.ref('board.board_my_dash_view').id:
            res['arch'] = self._inject_board_attributes(
                res['arch'], {'shareable': '1'})
        return res
