###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    def _context_get_partner(self):
        self.ensure_one()
        Partner = self.env['res.partner']
        partner = self._context.get('partner')
        if partner and isinstance(partner, int):
            partner = Partner.browse(partner)
        elif not partner and 'partner_id' in self._context:
            partner = Partner.browse(self._context['partner_id'])
        return partner

    def _get_applicable_rules_domain(self, products, date, **kwargs):
        domain = super()._get_applicable_rules_domain(products, date, **kwargs)
        partner = kwargs.get('partner') or self._context_get_partner()
        if partner and partner.industry_id:
            domain += [
                '|',
                ('partner_industry_id', '=', False),
                ('partner_industry_id', '=', partner.industry_id.id),
            ]
        else:
            domain += [
                ('partner_industry_id', '=', False),
            ]
        return domain
