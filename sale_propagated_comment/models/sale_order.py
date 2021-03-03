###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_propagated_comment = fields.Text(
        string='Propagated Comment',
    )

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super().onchange_partner_id()
        if not self.partner_id:
            return
        self.update({
            'sale_propagated_comment': self.partner_id.sale_propagated_comment
        })
