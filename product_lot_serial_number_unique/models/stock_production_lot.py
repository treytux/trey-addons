###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models
from odoo.exceptions import ValidationError


class ProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    @api.constrains('name', 'product_id')
    def _check_name_unique(self):
        lots = self.env['stock.production.lot'].search([
            ('product_id', '!=', self.product_id.id),
            ('name', '=', self.name),
        ])
        if lots:
            module = self.env['ir.module.module'].sudo().search([
                ('name', '=', 'stock_production_lot_multi_company'),
            ], limit=1)
            # Skip if installed and let multi company module to check
            # lot duplicity
            if module.state != 'installed':
                raise ValidationError(
                    _('This Lot/Serial number already exists in other '
                      'product!'))
