# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import api, models, fields


class ProductContractType(models.Model):
    _name = 'product.contract.type'
    _description = 'Product contract type'

    name = fields.Char(string='Nombre', required=True)
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product'
    )
    qty = fields.Float(
        string='Quantity',
        default=1
    )
    price_unit = fields.Float(
        string='Price unit'
    )
    tax_ids = fields.Many2many(
        comodel_name='account.tax',
        relation='product_contract_tax_rel',
        column1='product_contract_id',
        column2='tax_id'
    )
    contract_type_id = fields.Many2one(
        comodel_name='contract.type',
        string='Contract type'
    )

    @api.onchange('product_id')
    def onchange_product(self):
        if self.product_id:
            self.name = self.product_id.name
            self.price_unit =\
                self.product_id and self.product_id.list_price or 0
            self.tax_ids = [(
                6, 0, [tax.id for tax in self.product_id.taxes_id])]


class ContractType(models.Model):
    _name = 'contract.type'
    _description = 'Contract Type'

    name = fields.Char(string='Nombre', required=True)
    report_id = fields.Many2one(
        comodel_name='ir.actions.report.xml',
        string='Report',
        required=True,
        domain=[('usage', '=', 'contract')]
    )
    product_ids = fields.One2many(
        comodel_name='product.contract.type',
        inverse_name='contract_type_id',
        string='Products'
    )
