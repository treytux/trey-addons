###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    from_import_sale_amazon = fields.Boolean(
        string='From import sale Amazon',
        help='Internal field that will be marked when the sale orders are '
             'imported from the Amazon importer.\nIf this field is marked, '
             'when confirming the sales order, the usual carrier flow will be '
             'ignored and automatic order lines will not be generated with '
             'shipping costs.',
    )

    @api.multi
    def _action_confirm(self):
        res = super(SaleOrder, self)._action_confirm()
        for so in self:
            if so.from_import_sale_amazon:
                so.invoice_shipping_on_delivery = False
        return res
