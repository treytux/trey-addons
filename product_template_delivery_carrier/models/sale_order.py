from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_open_delivery_wizard(self):
        res = super().action_open_delivery_wizard()
        res['context'].update({
            'default_carrier_id' : []
        })
        return res
