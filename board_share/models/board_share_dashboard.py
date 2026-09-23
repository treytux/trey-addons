###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class BoardShareDashboard(models.Model):
    _name = 'board.share.dashboard'
    _description = 'Shared Dashboard'
    _order = 'create_date desc'

    name = fields.Char(
        string='Name',
        required=True,
    )
    owner_id = fields.Many2one(
        comodel_name='res.users',
        string='Owner',
        required=True,
        default=lambda self: self.env.user,
        readonly=True,
        index=True,
    )
    recipient_ids = fields.Many2many(
        comodel_name='res.users',
        relation='board_share_dashboard_res_users_rel',
        column1='dashboard_id',
        column2='user_id',
        string='Recipients',
    )
    view_id = fields.Many2one(
        comodel_name='ir.ui.view',
        string='Snapshot View',
        readonly=True,
        copy=False,
        ondelete='set null',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    is_owner = fields.Boolean(
        string='Is Owner',
        compute='_compute_is_owner',
    )

    @api.depends_context('uid')
    def _compute_is_owner(self):
        user = self.env.user
        for record in self:
            record.is_owner = record.owner_id == user

    @api.constrains('owner_id', 'recipient_ids')
    def _check_owner_not_recipient(self):
        for record in self:
            if record.owner_id in record.recipient_ids:
                raise ValidationError(
                    _('The owner cannot be a recipient of the shared '
                      'dashboard.')
                )

    def _get_snapshot_view_name(self):
        self.ensure_one()
        return 'Shared Dashboard: %s' % self.name

    def _get_personal_dashboard_arch(self):
        self.ensure_one()
        dashboard_view = self.env.ref('board.board_my_dash_view')
        board_view = self.env['board.board'].with_user(self.owner_id).get_view(
            dashboard_view.id, 'form')
        return board_view['arch']

    def _sync_snapshot_view(self):
        board_model = self.env['board.board']
        for record in self.filtered('view_id'):
            arch = board_model._prepare_shared_snapshot_arch(
                record.view_id.arch_db, record.name
            )
            record.view_id.sudo().write({
                'name': record._get_snapshot_view_name(),
                'arch_db': arch,
            })

    def _create_snapshot_view(self):
        board_model = self.env['board.board']
        for record in self.filtered(lambda dashboard: not dashboard.view_id):
            arch = board_model._prepare_shared_snapshot_arch(
                record._get_personal_dashboard_arch(), record.name)
            view = self.env['ir.ui.view'].sudo().create({
                'name': record._get_snapshot_view_name(),
                'model': 'board.board',
                'type': 'form',
                'arch_db': arch,
            })
            record.with_context(
                board_share_allow_system_fields=True
            ).sudo().write({
                'view_id': view.id
            })

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['owner_id'] = self.env.user.id
        records = super().create(vals_list)
        records._create_snapshot_view()
        return records

    def write(self, vals):
        if (
            not self.env.context.get('board_share_allow_system_fields')
            and ('owner_id' in vals or 'view_id' in vals)
        ):
            raise ValidationError(
                _('Owner and snapshot view cannot be modified manually.')
            )
        res = super().write(vals)
        if 'name' in vals:
            self._sync_snapshot_view()
        self._create_snapshot_view()
        return res

    def unlink(self):
        views = self.sudo().mapped('view_id')
        res = super().unlink()
        views.sudo().unlink()
        return res

    def action_open_board(self):
        self.ensure_one()
        self.check_access_rights('read')
        self.check_access_rule('read')
        if not self.active:
            raise UserError(_('This shared dashboard is archived.'))
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'board.board',
            'view_mode': 'form',
            'views': [(self.view_id.id, 'form')],
            'view_id': self.view_id.id,
            'target': 'current',
        }
