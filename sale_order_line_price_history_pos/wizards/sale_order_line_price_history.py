###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrderLinePriceHistory(models.TransientModel):
    _inherit = 'sale.order.line.price.history'

    pos_line_ids = fields.One2many(
        comodel_name='sale.order.line.price.history.line.pos',
        inverse_name='history_id',
        string='History lines',
        readonly=True,
    )

    @api.onchange('partner_id', 'include_quotations',
                  'include_commercial_partner')
    def _onchange_partner_id(self):
        super()._onchange_partner_id()
        self.pos_line_ids = False
        states = ['paid', 'done', 'invoiced']
        if self.include_quotations:
            states += ['draft']
        domain = [
            ('product_id', '=', self.product_id.id),
            ('state', 'in', states),
        ]
        if self.partner_id:
            if self.include_commercial_partner:
                domain += [('order_partner_id', 'child_of',
                            self.partner_id.commercial_partner_id.ids)]
            else:
                domain += [
                    ('order_partner_id', 'child_of', self.partner_id.ids)]
        vals = []
        lines = self.env['pos.order.line'].search(domain, limit=20)
        for line in lines:
            vals.append((0, False, {
                'pos_order_line_id': line.id,
                'history_sale_order_line_id': self.sale_order_line_id.id,
            }))
        self.pos_line_ids = vals


class SaleOrderLinePriceHistoryline(models.TransientModel):
    _name = 'sale.order.line.price.history.line.pos'
    _description = 'Sale order line price history POS line'

    history_id = fields.Many2one(
        comodel_name='sale.order.line.price.history',
        string='History',
    )
    history_sale_order_line_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='history sale order line',
    )
    pos_order_line_id = fields.Many2one(
        comodel_name='pos.order.line',
        string='pos order line',
    )
    order_id = fields.Many2one(
        related='pos_order_line_id.order_id',
    )
    partner_id = fields.Many2one(
        related='pos_order_line_id.order_partner_id',
    )
    date_order = fields.Datetime(
        related='pos_order_line_id.order_id.date_order',
    )
    qty = fields.Float(
        related='pos_order_line_id.qty',
    )
    price_unit = fields.Float(
        related='pos_order_line_id.price_unit',
    )
    discount = fields.Float(
        related='pos_order_line_id.discount',
    )

    def _prepare_set_price_history_vals(self):
        self.ensure_one()
        return {'price_unit': self.price_unit, 'discount': self.discount}

    @api.multi
    def action_set_price(self):
        self.ensure_one()
        self.history_sale_order_line_id.write(
            self._prepare_set_price_history_vals())
