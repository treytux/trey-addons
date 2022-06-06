###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountInvoiceLineByDefaultCode(models.TransientModel):
    _name = 'account.invoice.line.by.default.code'
    _description = 'Wizard to add and delete invoice lines'

    name = fields.Char(
        string='Name'
    )
    invoice_id = fields.Many2one(
        comodel_name='account.invoice',
        string='Invoice',
    )
    line_ids = fields.One2many(
        comodel_name='account.invoice.line.by.default.code.line',
        inverse_name='wizard_id',
        string='Lines',
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if 'invoice_id' not in res:
            res['invoice_id'] = self._context.get('active_ids', [False])[0]
        return res

    @api.multi
    def button_add_all_products(self):
        for line in self.line_ids:
            invoice_line = self.invoice_id.invoice_line_ids.filtered(
                lambda l: l.product_id.default_code == (
                    line.product_id.default_code))
            if invoice_line:
                invoice_line.write({
                    'quantity': invoice_line.quantity + 1,
                })
            else:
                category = line.product_id.categ_id
                invoice_line = self.env['account.invoice.line'].create({
                    'invoice_id': self.invoice_id.id,
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'account_id': category.property_account_income_categ_id.id,
                    'quantity': 1,
                    'price_unit': line.product_id.lst_price,
                })
                invoice_line._onchange_product_id()

    @api.multi
    def button_keep_only_wizard_products(self):
        lines = []
        for line in self.line_ids:
            invoice_line = self.invoice_id.invoice_line_ids.filtered(
                lambda l: l.product_id.default_code == (
                    line.product_id.default_code))
            if invoice_line:
                lines.append(invoice_line.id)
        lines = list(set(lines))
        for line in self.invoice_id.invoice_line_ids:
            if line.id not in lines:
                line.unlink()


class AccountInvoinceLineByDefaultCodeLine(models.TransientModel):
    _name = 'account.invoice.line.by.default.code.line'
    _description = 'Wizard line'

    name = fields.Char(
        string='Empty',
    )
    wizard_id = fields.Many2one(
        comodel_name='account.invoice.line.by.default.code',
        string='Wizard',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
    )
