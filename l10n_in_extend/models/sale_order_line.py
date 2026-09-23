###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('product_id', 'company_id')
    def _compute_tax_id(self):
        res = super()._compute_tax_id()
        for line in self:
            partner = line.order_id.partner_id
            product = line.product_id
            company = line.company_id
            if company.country_id and company.country_id.code != 'IN':
                continue
            if partner.country_id and partner.country_id.code != 'IN':
                continue
            if not company.state_id or not partner.state_id:
                raise UserError(_(
                    'Please, set state in customer and state in company.'))
            if not product or not product.hs_code_id:
                raise UserError(_('Please, set HS Code in product.'))
            if product.hs_code_id.rate == 'Nil':
                return res
            if partner.state_id.l10n_in_tin == company.state_id.l10n_in_tin:
                amount = float(product.hs_code_id.rate) / 2
                taxs = self.env['account.tax'].search([
                    ('type_tax_use', '=', 'sale'),
                    ('amount', '=', amount),
                    ('type_tax_use', '=', 'sale'),
                    '|',
                    ('name', '=ilike', '%SGST%'),
                    ('name', '=ilike', '%CGST%'),
                ])
            else:
                amount = float(product.hs_code_id.rate)
                taxs = self.env['account.tax'].search([
                    ('type_tax_use', '=', 'sale'),
                    ('amount', '=', amount),
                    ('name', '=ilike', '%IGST%'),
                ])
            line.tax_id = [(6, 0, taxs.ids)]
