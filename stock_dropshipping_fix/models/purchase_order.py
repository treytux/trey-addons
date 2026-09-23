###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _create_picking(self):
        res = super()._create_picking()
        for purchase in self:
            for picking in purchase.picking_ids.filtered(
                    lambda p: p.state not in ['cancel', 'done']):
                if picking.is_dropship and picking.sale_id and (
                        picking.sale_id.partner_shipping_id):
                    picking.supplier_id = picking.partner_id.id
                    picking.partner_id = picking.sale_id.partner_shipping_id.id
        return res
