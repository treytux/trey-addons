# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models, fields, exceptions, _


class WizProductLabelFromPurchase(models.TransientModel):
    _inherit = 'wiz.product.label'
    purchase_quantity = fields.Selection(
        selection=[('line', 'One label for each line'),
                   ('total', 'Total product quantity')],
        string='Quantity',
        default='total')
    purchase_include_service_product = fields.Boolean(
        string='Include service products',
        default=False)
    purchase_show_origin = fields.Boolean(
        string='Show origin',
        default=False,
        help='Show name purchase order in label.')

    @api.multi
    def button_print_from_purchase_label(self):
        moves = self.env['purchase.order.line'].search(
            [('order_id', 'in', self.env.context['active_ids'])])
        move_ids = []
        if self.purchase_quantity == 'line':
            move_ids = [
                m.id for m in moves
                if self.purchase_include_service_product or (
                    not self.purchase_include_service_product and
                    m.product_id and m.product_id.type not in 'service')]
        elif self.purchase_quantity == 'total':
            for m in moves:
                if self.purchase_include_service_product or (
                        not self.purchase_include_service_product and
                        m.product_id and m.product_id.type not in 'service'):
                    move_ids = move_ids + ([m.id] * int(m.product_qty))
        if not move_ids:
            raise exceptions.Warning(_('No labels for print'))
        return {'type': 'ir.actions.report.xml',
                'report_name': self.report_id.report_name,
                'datas': {'ids': move_ids},
                'context': {'render_func': 'render_product_purchase_label',
                            'report_name': self.report_id.report_name,
                            'show_origin': self.purchase_show_origin}}
