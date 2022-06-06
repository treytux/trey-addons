###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models
from odoo.tools.safe_eval import safe_eval


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(
        selection_add=[
            ('formula', 'Formula'),
        ],
    )
    formula = fields.Text(
        string='Formula',
        default='if len(order.order_line) > 1:\n'
                '   result = 5.99\n'
                'elif len(order.order_line) == 1:\n'
                '   result = 3.99\n',
    )

    def _get_formula_carrier_input_dict(self, order):
        return {
            'order': order,
        }

    def formula_rate_shipment(self, order):
        carrier = self._match_address(order.partner_shipping_id)
        if not carrier:
            return {
                'success': False,
                'price': 0.0,
                'error_message': 'Error: this delivery method is not '
                                 'available for this address.',
                'warning_message': False,
            }
        results = self._get_formula_carrier_input_dict(order)
        safe_eval(self.formula, results, mode="exec", nocopy=True)
        return {
            'success': True,
            'price': float(results['result']),
            'error_message': False,
            'warning_message': False,
        }
