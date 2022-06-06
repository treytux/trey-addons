###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        self.ensure_one()
        if not self.carrier_id and self.picking_type_id.carrier_required:
            raise ValidationError(_(
                'Picking must have a carrier assigned to it before '
                'being validated.'))
        return super().button_validate()
