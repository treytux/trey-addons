###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.constrains('comment_template_ids')
    def _check_is_condition_line_unique(self):
        condition_lines = self.comment_template_ids.filtered(
            lambda ln: ln.is_condition)
        if len(condition_lines) > 1:
            raise ValidationError(_(
                'Only one Terms and Conditions line can exist on a sales '
                'order.'))
