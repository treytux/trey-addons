###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    dachser_last_request = fields.Text(
        string='Last Dachser request',
        help='Used for issues debbuging',
        copy=False,
        readonly=True,
    )
    dachser_last_response = fields.Text(
        string='Last Dachser response',
        help='Used for issues debbuging',
        copy=False,
        readonly=True,
    )
    dachser_token = fields.Char(
        string='Dachser token',
        help='Dachser token to create label picking',
    )
    dachser_expedition_code = fields.Char(
        string='Dachser expedition code',
    )
    dachser_shipment_date = fields.Char(
        string='Dachser shipment date',
    )
    not_dachser_delivery_label = fields.Boolean(
        string='Not Dachser delivery label yet',
    )

    def _prepare_dachser_wizard(self):
        self.ensure_one()
        return {
            'picking_id': self.id,
        }

    def action_open_dachser_wizard(self):
        self.ensure_one()
        wizard_vals = self._prepare_dachser_wizard()
        wizard = self.env['delivery.dachser'].create(wizard_vals)
        action = self.env.ref(
            'delivery_dachser.delivery_dachser_wizard_action').read()[0]
        action['res_id'] = wizard.id
        action['context'] = self._context.copy()
        return action

    def action_get_dachser_label(self):
        self.ensure_one()
        self.write({
            'dachser_last_request': fields.Datetime.now(),
        })
        response = self.carrier_id.get_dachser_label(self, self.dachser_token)
        self.write({
            'tracking_number': response['tracking_number'],
            'exact_price': response['exact_price'],
            'dachser_expedition_code': response['dachser_expedition_code'],
            'dachser_shipment_date': response['dachser_shipment_date'],
            'dachser_token': response['dachser_token'],
            'dachser_last_response': fields.Datetime.now(),
        })
