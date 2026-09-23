###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_customerinfo_partner_ids(self):
        self.ensure_one()
        partner = self.partner_id
        if not partner:
            return []
        return (
            partner + partner.parent_id + partner.commercial_partner_id).ids

    def _check_customerinfo_lines_partner(self):
        for order in self:
            if not order.partner_id:
                continue
            partner_ids = order._get_customerinfo_partner_ids()
            invalid_lines = order.order_line.filtered(
                lambda line: (
                    line.customerinfo_id
                    and line.customerinfo_id.partner_id.id not in partner_ids))
            if not invalid_lines:
                continue
            raise ValidationError(_(
                'You cannot change the customer because these order lines '
                'use customer references that do not belong to %(partner)s: '
                '%(lines)s'
            ) % {
                'partner': order.partner_id.display_name,
                'lines': ', '.join(invalid_lines.mapped('display_name')), })

    @api.constrains('partner_id')
    def _constrain_customerinfo_lines_partner(self):
        self._check_customerinfo_lines_partner()
