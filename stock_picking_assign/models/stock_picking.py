###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    assign_id = fields.Many2one(
        comodel_name='res.users',
        domain='[("share", "=", False)]',
        string='Assigned user',
    )

    def assign_stock_picking_to_user(self):
        self.assign_id = self.env.user.id

    @api.constrains('assign_id')
    def _check_assign_id(self):
        for picking in self:
            if picking.assign_id and (
                    picking.assign_id.share is True):
                raise ValidationError(_('The user has to be of internal type'))
