###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields, api


class ContractContract(models.Model):
    _inherit = 'contract.contract'

    unit_id = fields.Many2one(
        comodel_name='product.business.unit',
        compute='_compute_unit_id',
        readonly=True,
        store=True,
        string='Business unit',
    )
    area_id = fields.Many2one(
        comodel_name='product.business.area',
        required=True,
        string='Area',
    )
    business_display_name = fields.Char(
        string='Business Display Name',
        compute='_compute_business_display_name',
    )

    @api.multi
    @api.depends('area_id')
    def _compute_unit_id(self):
        for contract in self:
            contract.unit_id = (
                contract.area_id.unit_id.id if contract.area_id else False)

    @api.multi
    @api.depends('unit_id', 'area_id')
    def _compute_business_display_name(self):
        display_name = self.env['product.template'].business_display_name_get
        for contract in self:
            contract.business_display_name = display_name(contract)

    @api.multi
    @api.constrains('unit_id', 'area_id')
    def _check_area_id(self):
        self.env['product.template'].check_area_id(self)

    @api.model
    def _finalize_invoice_creation(self, invoices):
        def get_account(invoice, account):
            acc = account.search([
                ('code', '=', account.code),
                ('company_id', '=', invoice.company_id.id)])
            return acc.id if acc else False

        for invoice in invoices:
            if invoice.company_id != invoice.account_id.company_id:
                invoice.account_id = get_account(invoice, invoice.account_id)
            for line in invoice.invoice_line_ids:
                if invoice.company_id != line.account_id.company_id:
                    line.account_id = get_account(invoice, line.account_id)
        return super()._finalize_invoice_creation(invoices)
