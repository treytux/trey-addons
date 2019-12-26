###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from openerp import fields, models


class ProductView(models.Model):
    _name = 'website.sale.product.view'
    _description = 'Ecommerce Product Views'
    _order = 'last_view_datetime DESC'
    _sql_constraints = [
        ('unique_session_product', 'UNIQUE(session_id, product_id)',
         'There is already a record for this product and session')
    ]

    session_id = fields.Char(
        string='Session ID',
        index=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.template',
        string='Product',
        required=True,
    )
    last_view_datetime = fields.Datetime(
        string='Last view datetime',
        default=fields.Datetime.now,
    )
