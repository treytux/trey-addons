###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    qty_total = fields.Float(
        string='Total units',
        compute='_compute_qty_total',
        help='Total units of the selected products.',
    )
    qty_total_done = fields.Float(
        string='Total units done',
        compute='_compute_qty_total',
        help='Total units of the selected products when done.',
    )

    @api.multi
    def action_send_confirmation_email(self):
        self.ensure_one()
        res = super().action_send_confirmation_email()
        commercial_partner_id = self.partner_id.commercial_partner_id
        if commercial_partner_id.delivery_slip_type == 'not_valued':
            return res
        res['context']['default_template_id'] = self.env.ref(
            'print_formats_picking.mail_delivery_valued_confirmation').id
        return res

    @api.depends('move_ids_without_package',
                 'move_ids_without_package.move_line_ids')
    def _compute_qty_total(self):
        for picking in self:
            if picking.state == 'done':
                picking.qty_total_done = sum(picking.move_line_ids.filtered(
                    lambda m: m.product_id.add_to_sum_qty).mapped('qty_done'))
            else:
                picking.qty_total = sum(picking.move_line_ids.filtered(
                    lambda m: m.product_id.add_to_sum_qty).mapped(
                    'product_uom_qty'))
