###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_default_stage(self):
        return self.env['sale.order.stage'].search(
            [], order='sequence', limit=1)

    stage_id = fields.Many2one(
        comodel_name='sale.order.stage',
        string='Stage',
        copy=False,
        default=_get_default_stage,
    )
    color = fields.Integer(
        string='Color Index',
    )

    def copy(self, default=None):
        if default is None:
            default = {}
        if not default.get('stage_id'):
            default['stage_id'] = self._get_default_stage().id
        return super().copy(default)
