###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class res_partner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def _purchase_invoice_count(self):
        super()._purchase_invoice_count()
        all_partners = self.search([('id', 'child_of', self.ids)])
        all_partners.read(['parent_id'])
        supplier_invoice_groups = self.env['account.invoice'].read_group(
            domain=[('partner_id', 'in', all_partners.ids),
                    ('type', '=', 'in_refund')],
            fields=['partner_id'], groupby=['partner_id']
        )
        for group in supplier_invoice_groups:
            partner = self.browse(group['partner_id'][0])
            while partner:
                if partner in self:
                    partner.supplier_invoice_count += group['partner_id_count']
                partner = partner.parent_id
