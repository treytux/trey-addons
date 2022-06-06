###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, fields, models
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_formed = fields.Boolean(
        string='Formed',
    )

    def update_is_formed(self):
        if self.state == 'assigned':
            self.is_formed = not self.is_formed
            if not self.is_formed:
                msg = _('Picking %s is not formed. User: %s - Date: %s') % (
                    self.name, self.env.user.name, fields.Datetime.now())
            else:
                msg = _('Picking %s is formed. User: %s - Date: %s') % (
                    self.name, self.env.user.name, fields.Datetime.now())
            self.message_post(body=msg)

    def action_done(self):
        for picking in self:
            if not picking.is_formed:
                raise ValidationError(_(
                    'Cannot validate picking %s without be formed') % (
                        picking.name))
        return super().action_done()
