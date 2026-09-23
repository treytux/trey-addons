###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    space_available = fields.Float(
        string='Space Available (GB)',
        default=1.0,
    )

    space_used = fields.Float(
        string='Space Used (GB)',
        compute='_compute_space_used',
    )

    def _compute_space_used(self):
        for user in self:
            if not user.id:
                user = self._origin
            files = self.env['ir.attachment'].search(
                [('create_uid', '=', user.id)])
            space_used = sum(
                [file.file_size / (1024 * 1024 * 1024) for file in files])
            user.space_used = not user.share and space_used or 0.0
