###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import re

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('partner_id')
    def _compute_note(self):
        super()._compute_note()
        for sale in self:
            if not sale.partner_id:
                continue
            if not sale.partner_id.sale_note:
                continue
            note = re.sub(r'<.*?>', '', sale.note or '').strip()
            if note:
                continue
            partner = sale.partner_id.with_context(lang=sale.partner_id.lang)
            sale.note = partner.sale_note
