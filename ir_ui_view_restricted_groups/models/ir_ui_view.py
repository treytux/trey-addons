###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class IrUiView(models.Model):
    _inherit = 'ir.ui.view'

    @api.model
    def default_view(self, model, view_type):
        res = super().default_view(model=model, view_type=view_type)
        domain = [
            ('model', '=', model),
            ('type', '=', view_type),
            ('mode', '=', 'primary'),
        ]
        views = self.env['ir.ui.view'].sudo().search(domain)
        for view in views:
            if not view.groups_id:
                return view.id
            view_groups = view.groups_id.ids
            for group in self.env.user.groups_id:
                if group.id in view_groups:
                    return view.id
        return res
