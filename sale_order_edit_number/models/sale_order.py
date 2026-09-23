###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    force_number = fields.Char(
        string='Force number',
        copy=False,
        groups='sale_order_edit_number.group_sale_order_force_number',
    )

    def _check_force_number_access(self):
        if not self.env.user.has_group(
                'sale_order_edit_number.group_sale_order_force_number'):
            raise AccessError(_(
                'You are not allowed to force the sale order number.'))

    def _force_number(self, vals):
        if 'name' in vals:
            return
        if vals.get('force_number'):
            self._check_force_number_access()
            if len(self) > 1:
                raise UserError(_(
                    'You cannot force the number on several sale orders at '
                    'once.'))
            domain = [('name', '=', vals['force_number'])]
            if self.ids:
                domain.append(('id', 'not in', self.ids))
            if self.sudo().search_count(domain):
                raise UserError(
                    _('Sale order number %s already exists!')
                    % vals['force_number'])
            vals['name'] = vals['force_number']

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._force_number(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._force_number(vals)
        return super().write(vals)
