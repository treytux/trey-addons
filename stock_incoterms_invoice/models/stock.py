# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api
import openerp.addons.decimal_precision as dp


class StockIncotermsInvoice(models.Model):
    _name = 'stock.incoterms.concept'
    _description = "Incoterms Concept"

    name = fields.Char(
        string="Name",
        required=True,
        translate=True)
    incoterm_id = fields.Many2one(
        comodel_name='stock.incoterms',
        string="Incoterms",
        required=True)
    product_id = fields.Many2one(
        comodel_name='product.template',
        string="Product",
        required=False,
        domain=[('type', '=', 'service')])
    in_invoice = fields.Boolean(
        string='Include in Invoice')
    price = fields.Float(
        string='Amount',
        digits=dp.get_precision('Account'))
    active = fields.Boolean(
        string='Active',
        default=True)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def _create_invoice_from_picking(self, picking, vals):
        res = super(StockPicking, self)._create_invoice_from_picking(
            picking, vals)
        if picking and picking.sale_id and picking.incoterm:
            concept_obj = self.env['stock.incoterms.concept']
            incoterm_obj = self.env['account.invoice.incoterm']
            concept_ids = concept_obj.search([('incoterm_id', '=',
                                               picking.incoterm.id)])
            if concept_ids:
                for concept in concept_ids:
                    vals = {
                        'concept_id': concept.id,
                        'price': concept.price,
                        'invoice_id': res,
                    }
                    incoterm_obj.create(vals)
        return res
