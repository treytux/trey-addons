###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    agreement_tmpl_ids = fields.Many2many(
        comodel_name='agreement.template',
        relation='product_template2agreement_template_rel',
        column1='product_template_id',
        column2='agreement_template_id',
        help='Agreement templates',
    )
