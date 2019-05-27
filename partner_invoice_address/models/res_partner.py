###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class Partner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def address_get(self, adr_pref=None):
        res = super().address_get(adr_pref)
        if 'invoice' not in res:
            return res
        invoice_partner = self.browse(res['invoice'])
        if invoice_partner.type == 'invoice':
            return res
        res['invoice'] = self.commercial_partner_id.id
        return res
