###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class DiscountGroup(models.Model):
    _name = 'discount.group'
    _description = 'Discount group'
    _order = 'sequence'

    name = fields.Char(
        string='Name',
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company.id,
    )
    date_start = fields.Datetime(
        string='Start',
        required=True,
        default=fields.Datetime.now,
    )
    date_end = fields.Datetime(
        string='End',
    )
    sequence = fields.Integer(
        string='Sequence',
    )
    discount = fields.Float(
        string='Discount',
    )
    partner_id = fields.Many2one(
        comodel_name='discount.partner.group',
        string='Partner group',
        required=True,
    )
    product_id = fields.Many2one(
        comodel_name='discount.product.group',
        string='Product group',
        required=True,
    )
