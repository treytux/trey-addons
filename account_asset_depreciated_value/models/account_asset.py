###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    value_pending_depreciated = fields.Float(
        string='Remaining depreciation value',
        copy=False,
    )
    date_pending_depreciated = fields.Date(
        string='Depreciation pending date',
        copy=False,
    )

    @api.depends('value_pending_depreciated')
    def _compute_depreciation(self):
        res = super()._compute_depreciation()
        for asset in self:
            lines = asset.depreciation_line_ids.filtered(
                lambda line: line.type in ('depreciate', 'remove') and (
                    line.init_entry or line.move_check))
            value_depreciated = sum([line.amount for line in lines])
            if value_depreciated == 0:
                depreciated = asset.value_pending_depreciated
                residual = (
                    asset.depreciation_base - asset.value_pending_depreciated)
            else:
                depreciated = value_depreciated + (
                    asset.value_pending_depreciated)
                residual = asset.depreciation_base - value_depreciated - (
                    asset.value_pending_depreciated)
            asset.update({
                'value_residual': residual,
                'value_depreciated': depreciated
            })
        return res

    def compute_depreciation_board(self):
        res = super().compute_depreciation_board()
        if not self.value_pending_depreciated or (
                not self.date_pending_depreciated):
            return res
        if not self.depreciation_line_ids[-1].previous_id:
            return res
        last_amount = self.depreciation_line_ids[-1].previous_id.remaining_value
        self.depreciation_line_ids[-1].amount = last_amount
        lines = self.depreciation_line_ids.filtered(
            lambda ln: ln.remaining_value < 0 or ln.amount < 0 or (
                ln.remaining_value == 0 and ln.amount == 0))
        if len(lines) == 1:
            lines.unlink()
        elif len(lines) > 1:
            lines[1:].unlink()
        last_amount = self.depreciation_line_ids[-1].previous_id.remaining_value
        self.depreciation_line_ids[-1].amount = last_amount
        return res

    def _compute_depreciation_table(self):
        table = super()._compute_depreciation_table()
        if not self.value_pending_depreciated or (
                not self.date_pending_depreciated):
            return table
        new_table = []
        for entry in table:
            new_list = []
            for line in entry['lines']:
                if line['date'] > self.date_pending_depreciated:
                    new_list.append(line)
            if not new_list:
                continue
            new_table.append(entry)
            last_entry = new_table[-1]
            last_entry['lines'] = new_list
        return new_table

    def _create_first_asset_line(self):
        res = super()._create_first_asset_line()
        if not self.value_pending_depreciated:
            return res
        asset_line = self.env['account.asset.line'].search([
            ('asset_id', '=', self.id),
        ], limit=1)
        asset_line.amount = self.purchase_value - self.value_pending_depreciated
        asset_line.depreciated_value = self.value_pending_depreciated
        if self.date_pending_depreciated:
            asset_line.line_date = self.date_pending_depreciated
        return res
