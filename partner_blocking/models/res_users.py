###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class Users(models.Model):
    _inherit = 'res.users'

    allowed = fields.Boolean(
        comodel_name='res.partner',
        related='partner_id.allowed',
        string='Allowed',
        help='If checked, user can log in into system.')

    @api.multi
    def toggle_allowed(self):
        for record in self:
            record.partner_id._allowed_set(not record.allowed, 'user')
            record._invalidate_session_cache()

    def _get_session_token_fields(self):
        if not self.allowed:
            return {'id'}
        return super()._get_session_token_fields()
