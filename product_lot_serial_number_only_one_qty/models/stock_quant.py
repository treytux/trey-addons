###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models
from odoo.exceptions import ValidationError


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.constrains('quantity')
    def check_quantity(self):
        super().check_quantity()
        for quant in self:
            if quant.product_id.tracking != 'serial':
                continue
            quants = self.search([
                ('product_id', '=', quant.product_id.id),
                ('lot_id', '=', quant.lot_id.id),
                ('location_id.usage', '=', 'internal'),
                ('quantity', '>=', 1),
                ('id', '!=', quant.id),
            ])
            if not quants:
                continue
            raise ValidationError(_(
                'Product "%s" is serial number tracked, and it is not '
                'possible for more than one unit to be in stock.\nIn this '
                'case the lot that already exists is %s.') % (
                    quant.product_id.name, quant.lot_id.name))
