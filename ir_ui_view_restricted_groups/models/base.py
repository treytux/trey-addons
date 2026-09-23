###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class Base(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        if view_id:
            view = self.env['ir.ui.view'].sudo().browse(view_id)
            if view.groups_id:
                view_groups = view.groups_id.ids
                for group in self.env.user.groups_id:
                    if group.id in view_groups:
                        return super()._get_view(view_id, view_type, **options)
                return super()._get_view(None, view_type, **options)
        return super()._get_view(view_id, view_type, **options)

    @api.model
    def _get_view_cache_key(self, view_id=None, view_type='form', **options):
        res = super()._get_view_cache_key(view_id, view_type, **options)
        return res + (self.env.user,)
