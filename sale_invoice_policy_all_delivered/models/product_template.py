###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    invoice_policy = fields.Selection(
        selection_add=[
            ('all_delivered', 'All delivered'),
        ],
        ondelete={
            'all_delivered': lambda records: records.write({
                'invoice_policy': 'delivery',
            }),
        },
    )
