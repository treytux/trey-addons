###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from openerp import _, api, fields, models


class WizStockRotation(models.TransientModel):
    _name = 'wiz.stock.rotation'
    _description = 'Wizard to stock rotation report'

    name = fields.Char(
        string='Empty',
    )
    date_from = fields.Date(
        string='Date from',
        default=fields.Date.today(),
        required=True,
    )
    date_to = fields.Date(
        string='Date to',
        default=fields.Date.today(),
        required=True,
    )
    product_category_id = fields.Many2one(
        comodel_name='product.category',
        string='Product category',
    )

    @api.multi
    def action_accept(self):
        ctx = self.env.context.copy()
        ctx.update({
            'search_default_product_categ_id': (
                self.product_category_id and self.product_category_id.id
                or None)})
        return {
            'name': _('Stock Rotation'),
            'domain': "[('date_day', '>=', '%s'), ('date_day', '<=', '%s')]" % (
                self.date_from, self.date_to),
            'view_type': 'form',
            'view_mode': 'pivot',
            'res_model': 'stock.rotation.report',
            'type': 'ir.actions.act_window',
            'context': ctx,
        }
