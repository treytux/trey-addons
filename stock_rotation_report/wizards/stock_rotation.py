# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, _


class WizStockRotation(models.TransientModel):
    _name = 'wiz.stock.rotation'
    _description = 'Wizard to stock rotation report'

    @api.model
    def _get_year_init(self):
        today_str = fields.Date.context_today(self)
        today = fields.Date.from_string(today_str)
        return today.replace(day=1, month=1)

    name = fields.Char(
        string='Empty')
    date_from = fields.Date(
        string='Date from',
        default=_get_year_init,
        required=True)
    date_to = fields.Date(
        string='Date to',
        default=fields.Date.context_today,
        required=True)
    product_category_id = fields.Many2one(
        comodel_name='product.category',
        string='Product category')

    @api.multi
    def action_accept(self):
        ctx = self.env.context.copy()
        ctx.update({
            'search_default_product_categ_id': (
                self.product_category_id and self.product_category_id.id or
                None)})
        return {
            'name': _('Stock Rotation'),
            'domain': "[('date', '>=', '%s'), ('date', '<=', '%s')]" % (
                self.date_from, self.date_to),
            'view_type': 'form',
            'view_mode': 'graph',
            'res_model': 'stock.rotation.report',
            'type': 'ir.actions.act_window',
            'context': ctx}
