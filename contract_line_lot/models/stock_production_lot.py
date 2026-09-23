###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models


class StockProductionLot(models.Model):
    _inherit = 'stock.lot'

    contract_line_ids = fields.Many2many(
        comodel_name='contract.line',
        string='Contract lines',
        compute='_compute_contract_line_ids',
    )
    last_contract_id = fields.Many2one(
        comodel_name='contract.contract',
        string='Contract',
    )
    last_contract_line_id = fields.Many2one(
        comodel_name='contract.line',
        string='Contract line',
        compute='_compute_contract_line_ids',
        compute_sudo=True,
        store=True,
    )
    last_contract_product_id = fields.Many2one(
        comodel_name='product.product',
        related='last_contract_line_id.product_id',
        string='Product',
    )
    last_contract_date_start = fields.Date(
        related='last_contract_line_id.date_start',
        string='Date start',
    )
    last_contract_date_end = fields.Date(
        related='last_contract_line_id.date_end',
        string='Date end',
    )
    last_location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location',
        compute='_compute_last_location_id',
    )

    @api.depends('quant_ids', 'quant_ids.location_id')
    def _compute_last_location_id(self):
        for lot in self:
            lot.last_location_id = lot.quant_ids[-1:].location_id or False

    @api.depends('quant_ids')
    def _compute_contract_line_ids(self):
        for lot in self:
            lines = self.env['contract.line'].search([
                ('lot_ids', 'in', lot.id),
            ])
            lot.contract_line_ids = [(6, 0, lines.ids)]
            if not lines:
                lot.last_contract_line_id = False
                lot.write({'last_contract_id': False})
                continue
            lot.last_contract_line_id = lines[0].id
            lot.write({'last_contract_id': lines[0].contract_id.id})

    def action_show_contract_lines_lot(self):
        contract_ids = self.contract_line_ids.mapped('contract_id').ids
        form_view = self.env.ref('contract.contract_contract_form_view')
        tree_view = self.env.ref('contract.contract_contract_tree_view')
        search_view = self.env.ref('contract.contract_contract_search_view')
        action_vals = {
            'name': _('Contract'),
            'res_model': 'contract.contract',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree, form',
            'search_view_id': search_view.id,
            'view_type': 'form',
            'domain': [('id', 'in', contract_ids)],
        }
        if len(contract_ids) == 1:
            del action_vals['views']
            action_vals.update({
                'view_mode': 'form',
                'res_id': contract_ids[0],
            })
        return action_vals
