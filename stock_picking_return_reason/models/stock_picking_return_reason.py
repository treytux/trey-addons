###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockPickingReturnReason(models.Model):
    _name = 'stock.picking.return.reason'
    _description = 'Stock picking return reason'

    name = fields.Char(
        string='Reason name',
        required=True,
    )
    description = fields.Char(
        string='Reason description',
    )
    picking_ids = fields.One2many(
        comodel_name='stock.picking',
        inverse_name='return_reason_id',
        string='Pickings',
        readonly=True,
    )
    pickings_count = fields.Integer(
        string='Pickings count',
        compute='_compute_pickings_count',
    )

    @api.constrains('name')
    def _check_name_unique(self):
        for reason in self:
            reasons = self.env['stock.picking.return.reason'].search([
                ('name', '=', reason.name),
                ('id', '!=', reason.id),
            ])
            if reasons:
                raise ValidationError(_('The reason name must be unique!'))

    @api.depends('picking_ids')
    def _compute_pickings_count(self):
        for reason in self:
            reason.pickings_count = len(reason.picking_ids)

    def action_view_pickings_reason(self):
        form_view = self.env.ref('stock.view_picking_form')
        tree_view = self.env.ref('stock.vpicktree')
        search_view = self.env.ref('stock.view_picking_internal_search')
        action_vals = {
            'name': _('Stock pickings'),
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree,form',
            'search_view_id': search_view.id,
            'view_type': 'form',
            'domain': [('id', 'in', self.picking_ids.ids)],
        }
        if len(self.picking_ids) == 1:
            del action_vals['views']
            action_vals.update({
                'view_mode': 'form',
                'res_id': self.picking_ids[0].id,
            })
        return action_vals
