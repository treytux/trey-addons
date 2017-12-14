# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api, _
from openerp.addons.decimal_precision import decimal_precision as dp


class ProductListPriceHistorical(models.Model):
    _name = 'product.listprice.history'
    _rec_name = 'date'
    _order = 'date desc'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=_get_company,
        required=True)
    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string="Product",
        required=False)
    date = fields.Datetime(
        string='Historization Time',
        default=fields.Datetime.now(),
        required=False)
    list_price = fields.Float(
        string='Sale Price',
        digits_compute=dp.get_precision('Product Price'))


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    price_history_ids = fields.One2many(
        comodel_name='product.listprice.history',
        inverse_name='product_tmpl_id',
        string="Historical Price",
        ondelete='cascade',
        required=False)

    @api.multi
    def open_listprice_history(self):
        view = self.env.ref(
            'product_listprice_history.product_template_listprice_form')

        return {
            'name': _('Sales Price History'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'product.template',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': self.env.context,
            'res_id': self.id,
        }

    def write(self, cr, uid, ids, vals, context=None):
        result = super(ProductTemplate, self).write(cr, uid, ids, vals,
                                                    context=context)
        if 'list_price' in vals:
            for template in self.browse(cr, uid, ids, context=context):
                values = {
                    'product_tmpl_id': template.id,
                    'list_price': template.list_price,
                }
            self.pool['product.listprice.history'].create(cr, uid, values)
        return result
