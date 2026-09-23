###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    @api.model
    def _get_domain_return_reason_id(self):
        active_model = self.env.context.get('active_model', False)
        active_id = self.env.context.get('active_id', False)
        if active_model != 'stock.picking' or not active_id:
            return False
        picking = self.env[active_model].browse(active_id)
        carriers = self.env['delivery.carrier'].search([
            '|',
            ('company_id', '=', False),
            ('company_id', '=', self.env.company.id),
        ])
        available_carriers = carriers.available_carriers(
            picking.partner_id) if picking.partner_id else carriers
        return_reasons = self.env['stock.picking.return.reason'].search([
            '|',
            ('carrier_id', '=', False),
            ('carrier_id', 'in', available_carriers.ids),
        ])
        return [('id', 'in', return_reasons.ids)]

    return_reason_id = fields.Many2one(
        comodel_name='stock.picking.return.reason',
        string='Return reason',
        domain=_get_domain_return_reason_id,
    )

    def _create_returns(self):
        new_picking_id, pick_type_id = super()._create_returns()
        new_picking = self.env['stock.picking'].browse(new_picking_id)
        if not self.return_reason_id.carrier_id:
            return new_picking_id, pick_type_id
        carrier = self.return_reason_id.carrier_id
        if carrier.delivery_type in ['fixed', 'base_on_rule']:
            vals = carrier.rate_shipment(new_picking.sale_id)
            price = vals['price']
        else:
            price = 0
        new_picking.write({
            'carrier_id': carrier.id,
            'carrier_price': price,
        })
        values = new_picking.sale_id._prepare_delivery_line_vals(
            carrier, price)
        sale_line = self.env['sale.order.line'].sudo().create(values)
        sale_line.is_delivery_return = True
        sale_line.name = _('Return picking %s - %s') % (
            new_picking.name, sale_line.name)
        return new_picking_id, pick_type_id
