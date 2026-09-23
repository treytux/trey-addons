###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    line_goods_free_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Goods free parent line',
        help='Sale line on which the goods free are dependent. '
             'To set product goods free manually, a line from the sale of the '
             'same product must be set in this field.',
    )

    def partner_for_goods_free(self):
        order = self.mapped('order_id')
        order.ensure_one()
        partner = order.partner_id
        while True:
            if partner.goods_free_ids:
                return partner
            if partner.company_type == 'company':
                break
            if not partner.parent_id:
                break
            partner = partner.parent_id
        return partner

    def create_goods_free(self):
        self.ensure_one()
        if not self.product_id:
            return self
        partner = self.partner_for_goods_free()
        if not partner.goods_free_ids:
            return self
        agreement = partner.goods_free_ids.filtered(
            lambda g: g.product_id == self.product_id)
        if not agreement:
            return self
        free_qty = round(
            round(self.product_uom_qty * (agreement.percent / 100), 1))
        if free_qty < 1:
            return self
        data = self._convert_to_write(self._cache)
        data.update({
            'name': '\n'.join([self.name, _('(Goods free)')]),
            'sequence': self.sequence + 0.0001,
            'line_goods_free_id': self.id,
            'product_uom_qty': free_qty,
            'discount': 100,
        })
        if 'agents' in self._fields:
            data['agents'] = [(5, 0, 0)]
        return self.with_context(no_add_goods_free=True).create(data)

    def _prepare_agents_vals(self, vals=None):
        if 'agents' not in self._fields:
            return []
        if self.line_goods_free_id or (vals or {}).get('line_goods_free_id'):
            return []
        return super()._prepare_agents_vals(vals=vals)

    @api.model
    def create(self, vals):
        line = super().create(vals)
        if self._context.get('no_add_goods_free'):
            return line
        line.create_goods_free()
        return line

    def write(self, vals):
        res = super().write(vals)
        if self._context.get('no_check_goods_free'):
            return res
        for line in self:
            free_line = line.order_id.order_line.filtered(
                lambda ln: ln.line_goods_free_id == line)
            if 'product_id' in vals and line.line_goods_free_id:
                line.unlink()
            elif 'product_id' in vals and not line.line_goods_free_id:
                line.create_goods_free()
            elif free_line:
                free_line.with_context(no_check_goods_free=True).write({
                    'discount': 100,
                    'price_unit': line.price_unit,
                    'tax_id': [(6, 0, line.tax_id.ids)],
                })
            elif line.line_goods_free_id:
                line.with_context(no_check_goods_free=True).write({
                    'discount': 100,
                    'price_unit': line.line_goods_free_id.price_unit,
                    'tax_id': [(6, 0, line.line_goods_free_id.tax_id.ids)],
                })
        return res
