# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api
from openerp.addons import decimal_precision as dp


class WizProductConfig(models.TransientModel):
    _name = 'wiz.product.config'
    _description = 'Wizard product configuration.'

    @api.model
    def _get_dimension_uom_domain(self):
        return [
            ('category_id', '=', self.env.ref('product.uom_categ_length').id)]

    name = fields.Char(
        string='Empty')
    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Product template')
    uom_id = fields.Many2one(
        comodel_name='product.uom',
        string='Unit of Measure',
        help='Default Unit of Measure used for all stock operation.')
    list_price = fields.Float(
        string='Sale Price',
        digits=dp.get_precision('Product Price'))
    dimensional_uom_id = fields.Many2one(
        comodel_name='product.uom',
        string='Dimensional UoM',
        domain=_get_dimension_uom_domain,
        help='UoM for length, height, width',
        required=True)
    length = fields.Float(
        string='Length (in m)',
        digits=dp.get_precision('Product UoS'),
        required=True)
    height = fields.Float(
        string='Height (in m)',
        digits=dp.get_precision('Product UoS'),
        required=True)
    width = fields.Float(
        string='Width (in m)',
        digits=dp.get_precision('Product UoS'),
        required=True)
    uos_id = fields.Many2one(
        comodel_name='product.uom',
        string='Unit of Sale',
        help='Specify a unit of measure here if invoicing is made in another '
             'unit of measure than inventory. Keep empty to use the default '
             'unit of measure.',
        required=True)
    price_unit_uos = fields.Float(
        string='Price in unit of sale',
        digits=dp.get_precision('Product Price'),
        required=True)
    uos_coeff = fields.Float(
        string='Unit of Measure -> UOS Coeff',
        digits=dp.get_precision('Product UoS'),
        help='Coefficient to convert default Unit of Measure to Unit of Sale\n'
             'uos = uom * coeff',
        required=True)

    @api.model
    def default_get(self, fields):
        res = super(WizProductConfig, self).default_get(fields)
        product_tmpl = self.env['product.template'].browse(
            self.env.context['active_id'])
        res.update({
            'product_tmpl_id': product_tmpl.id,
            'uom_id': product_tmpl.uom_id.id,
            'list_price': product_tmpl.list_price,
            'dimensional_uom_id': (
                product_tmpl.dimensional_uom_id and
                product_tmpl.dimensional_uom_id.id or None),
            'length': product_tmpl.length,
            'height': product_tmpl.height,
            'width': product_tmpl.width,
            'uos_id': product_tmpl.uos_id and product_tmpl.uos_id.id or None,
            'price_unit_uos': product_tmpl.price_unit_uos,
            'uos_coeff': product_tmpl.uos_coeff})
        return res

    @api.multi
    def compute(self, compute_coeff=True):
        self.ensure_one()
        if compute_coeff:
            self.uos_coeff = self.length * self.height
            self.uos_coeff *= self.width and self.width or 1
        self.list_price = self.price_unit_uos * self.uos_coeff

    @api.onchange('dimensional_uom_id', 'length', 'height', 'width',
                  'uos_id')
    def onchange_dimensions(self):
        self.compute()

    @api.onchange('uos_coeff', 'price_unit_uos')
    def onchange_coeff(self):
        self.compute(compute_coeff=False)

    @api.multi
    def button_accept(self):
        self.ensure_one()
        self.compute()
        self.product_tmpl_id.write({
            'list_price': self.list_price,
            'dimensional_uom_id': self.dimensional_uom_id.id,
            'length': self.length,
            'height': self.height,
            'width': self.width,
            'uos_id': self.uos_id.id,
            'price_unit_uos': self.price_unit_uos,
            'uos_coeff': self.uos_coeff})
        return {'type': 'ir.actions.act_window_close'}
