###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ContractLineExtra(models.Model):
    _name = 'contract.line.extra'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Contract line extra'

    name = fields.Char(
        string='Name',
        translate=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company.id,
    )
    contract_id = fields.Many2one(
        comodel_name='contract.contract',
        string='Contract',
        required=True,
        ondelete='cascade',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
    )
    quantity = fields.Float(
        string='Quantity',
        digits='Product Unit of Measure',
        default=1,
    )
    price_unit = fields.Float(
        string='Price unit',
        digits='Product Price',
    )
    date_to_invoice = fields.Date(
        string='Date to invoice',
        default=fields.Date.today(),
        help='Date on which this line will be invoiced.',
    )
    invoice_id = fields.Many2one(
        comodel_name='account.move',
        string='Invoice',
        readonly=True,
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if not self.product_id:
            return
        self.name = self.product_id.display_name
        fiscal_position = (
            self.contract_id.partner_id.property_account_position_id)
        self.price_unit = self.product_id._get_tax_included_unit_price(
            self.company_id,
            self.contract_id.currency_id,
            None,
            'sale',
            fiscal_position=fiscal_position,
            product_uom=self.product_id.uom_id,
        )

    def _prepare_invoice_line(self):
        self.ensure_one()
        return {
            'name': self.name,
            'product_id': self.product_id.id,
            'quantity': self.quantity,
            'price_unit': self.price_unit,
            'contract_line_extra_id': self.id,
        }
