###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    pack_component_cost = fields.Selection(
        selection=[
            ('detailed', 'Detailed per component'),
            ('ignored', 'Ignored components costs'),
            ('totalized', 'Totalized in main product'),
        ],
        help='On sale orders:\n'
             '* Detailed per component: Detail lines with costs.\n'
             '* Totalized in main product: Detail lines merging '
             ' lines costs on pack.\n'
             '* Ignored: Use product pack cost (ignore detail line costs).',
        string='Pack component cost',
        default='totalized',
        required=True,
    )

    @api.depends(
        'pack_line_ids', 'pack_line_ids.product_id',
        'pack_line_ids.product_id.standard_price')
    def _compute_standard_price(self):
        super()._compute_standard_price()
        for template in self:
            if (not template.pack_ok or not template.pack_line_ids
                    or not template.pack_component_cost == 'totalized'
                    or len(template.product_variant_ids) > 1):
                continue
            template.standard_price = (
                sum(line.product_id.standard_price * line.quantity
                    for line in template.pack_line_ids))
