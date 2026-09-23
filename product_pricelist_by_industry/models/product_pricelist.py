###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


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

    @api.multi
    def _get_rules_sql(self, products, date):
        _select, _from, _where, _orderby, params = super()._get_rules_sql(
            products, date)
        partner = self._context_get_partner()
        if not partner or not partner.industry_id:
            return _select, _from, _where, _orderby, params
        _where += (
            'AND (item.partner_industry_id IS NULL '
            'OR item.partner_industry_id = %s) '
        )
        params.append(partner.industry_id.id)
        return _select, _from, _where, _orderby, params

    @api.multi
    def _is_valid_rule(self, rule, product, qty):
        is_valid = super()._is_valid_rule(rule, product, qty)
        if not is_valid:
            return is_valid
        if rule.applied_on != '2_industry':
            return is_valid
        partner = self._context_get_partner()
        if partner and partner.industry_id == rule.partner_industry_id:
            return True
        return False
