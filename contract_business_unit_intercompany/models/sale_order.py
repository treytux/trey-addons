###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def _prepare_contract_value(self, contract_template):
        res = super()._prepare_contract_value(contract_template)
        if not contract_template.unit_id:
            return res
        invoice_obj = self.env['account.invoice']
        company = contract_template.unit_id.company_id
        res['company_id'] = company.id
        if contract_template.area_id:
            res['area_id'] = contract_template.area_id.id
        if 'payment_term_id' in res:
            payment = self.env['account.payment.term'].browse(
                res['payment_term_id'])
            res['payment_term_id'] = invoice_obj.intercompany_get_id(
                payment, company)
        if 'payment_mode_id' in res:
            mode = self.env['account.payment.mode'].browse(
                res['payment_mode_id'])
            res['payment_mode_id'] = invoice_obj.intercompany_get_id(
                mode, company)
        return res
