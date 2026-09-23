###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _get_computed_taxes(self):
        taxes = super()._get_computed_taxes()
        self.ensure_one()
        move = self.move_id
        if move.move_type not in (
                'out_invoice', 'out_refund', 'in_invoice', 'in_refund'):
            return taxes
        partner = move.partner_id
        company = move.company_id
        if company.country_id and company.country_id.code != 'IN':
            return taxes
        if partner.country_id and partner.country_id.code != 'IN':
            return taxes
        if not company.state_id or not partner.state_id:
            if move.is_sale_document():
                raise UserError(_(
                    'Please, set state in customer and state in company.'))
            raise UserError(_(
                'Please, set state in vendor and state in company.'))
        if not self.product_id or not self.product_id.hs_code_id:
            raise UserError(_('Please, set HS Code in product.'))
        if self.product_id.hs_code_id.rate == 'Nil':
            return taxes
        tax_use = 'sale' if move.is_sale_document() else 'purchase'
        if partner.state_id.l10n_in_tin == company.state_id.l10n_in_tin:
            amount = float(self.product_id.hs_code_id.rate) / 2
            domain = [
                ('company_id', '=', company.id),
                ('type_tax_use', '=', tax_use),
                ('amount', '=', amount),
                '|',
                ('name', '=ilike', '%SGST%'),
                ('name', '=ilike', '%CGST%'),
            ]
        else:
            amount = float(self.product_id.hs_code_id.rate)
            domain = [
                ('company_id', '=', company.id),
                ('type_tax_use', '=', tax_use),
                ('amount', '=', amount),
                ('name', '=ilike', '%IGST%'),
            ]
        return self.env['account.tax'].search(domain)
