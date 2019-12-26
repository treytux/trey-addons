###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields


class SaleCustomizationLine(models.Model):
    _name = 'sale.customization.line'
    _description = 'Sale customization line'
    _order = 'name'

    name = fields.Char(
        string='Name',
        required=True)
    image = fields.Binary(
        string='Image')
    customization_id = fields.Many2one(
        comodel_name='sale.customization',
        string='customization')
    position_id = fields.Many2one(
        comodel_name='sale.customization.position',
        required=True,
        string='Position')
    type_id = fields.Many2one(
        comodel_name='sale.customization.type',
        required=True,
        string='Type')
    description = fields.Text(
        string='Description')
