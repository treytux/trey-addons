###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import odoo.addons.decimal_precision as dp
from odoo import api, fields, models


class ConnectorSimulatorSale(models.TransientModel):
    _name = 'connector.simulator.sale'
    _description = 'Wizard to simulate sale'

    state = fields.Selection(
        string='State',
        selection=[
            ('step_1', 'Step 1'),
            ('step_2', 'Step 2'),
            ('step_done', 'Done'),
        ],
        required=True,
        default='step_1',
    )
    order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        required=True,
        ondelete='cascade',
    )
    lines = fields.One2many(
        comodel_name='connector.simulator.sale.line',
        inverse_name='sale_id',
        string='Lines',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.user.company_id,
    )
    supplier_mode = fields.Selection(
        selection=[],
        string='Supplier mode',
    )

    @api.multi
    def action_to_step_2(self):
        self.state = 'step_2'
        return self._reopen_view()

    @api.multi
    def action_to_step_done(self):
        self.state = 'step_done'
        return self._reopen_view()

    @api.multi
    def _reopen_view(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.ids[0],
            'res_model': self._name,
            'target': 'new',
            'context': {},
        }


class ConnectorSimulatorSaleLine(models.TransientModel):
    _name = 'connector.simulator.sale.line'
    _description = 'Simulator sale line'

    sale_id = fields.Many2one(
        comodel_name='connector.simulator.sale',
        string='Sale order',
        required=True,
        ondelete='cascade',
    )
    sale_line_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Sale line',
    )
    cost_price = fields.Float(
        string='Odoo Cost',
        digits=dp.get_precision('Product Price'),
    )
    product_uom_qty = fields.Float(
        related='sale_line_id.product_uom_qty',
    )
    product_uom = fields.Many2one(
        related='sale_line_id.product_uom',
    )
    product_id = fields.Many2one(
        related='sale_line_id.product_id',
    )
    product_list_price = fields.Float(
        related='sale_line_id.product_id.list_price',
    )
    discount = fields.Float(
        string='Discount',
    )
    price_unit = fields.Float(
        string='Price unit',
    )
    line_color = fields.Selection(
        string='Color',
        selection=[
            ('red', 'Red'),
            ('orange', 'Orange'),
            ('green', 'Green'),
            ('blue', 'Blue'),
        ],
        compute='_compute_line_color',
    )

    def _compute_line_color(self):
        return True
