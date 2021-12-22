###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    signature_device = fields.Many2one(
        comodel_name='iot.device',
        string='Signature device',
    )
    signature = fields.Binary(
        string='Signature',
        help='Digitized signature',
    )
    photo_user = fields.Binary(
        string='Photo',
        help='Photo of the user who signs the delivery note',
    )

    def button_signed(self):
        self.signature_device = self.env.user.signed_device

    def sign_stock_picking(self, value):
        context = dict(self.env.context)
        picking = self.env['stock.picking'].search([
            ('signature_device.id', '=', context.get('iot_device_id'))])
        if picking:
            picking.signature = value['signature']
            picking.photo_user = value['photo']
            picking.signature_device = False
            return {'value': value}
