###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    invoice_by_product_categ_ids = fields.Many2many(
        comodel_name='product.category',
        relation='product_category2res_partner_rel',
        column1='partner_id',
        column2='product_category_id',
        string='Separated invoices by categories',
    )
