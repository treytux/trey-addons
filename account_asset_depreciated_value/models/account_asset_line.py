###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class AccountAssetLine(models.Model):
    _inherit = 'account.asset.line'

    @api.depends('amount', 'previous_id', 'type')
    @api.multi
    def _compute_values(self):
        res = super()._compute_values()
        dlines = self
        if self.env.context.get('no_compute_asset_line_ids'):
            exclude_ids = self.env.context['no_compute_asset_line_ids']
            dlines = self.filtered(lambda ln: ln.id not in exclude_ids)
        dlines = dlines.filtered(lambda ln: ln.type == 'depreciate')
        dlines = dlines.sorted(key=lambda ln: ln.line_date)
        asset_ids = dlines.mapped('asset_id')
        grouped_dlines = []
        for asset in asset_ids:
            grouped_dlines.append(
                dlines.filtered(lambda ln: ln.asset_id.id == asset.id))
        for dlines in grouped_dlines:
            for i, dl in enumerate(dlines):
                if i == 0:
                    depreciation_base = dl.depreciation_base
                    if not dl.previous_id:
                        tmp = dl.asset_id.value_residual
                    else:
                        tmp = depreciation_base - dl.previous_id.remaining_value
                    depreciated_value = dl.previous_id and tmp or (
                        dl.asset_id.value_pending_depreciated or 0.0)
                    remaining_value = \
                        depreciation_base - depreciated_value - dl.amount
                else:
                    depreciated_value += dl.previous_id.amount
                    remaining_value -= dl.amount
                dl.depreciated_value = depreciated_value
                dl.remaining_value = remaining_value
        return res
