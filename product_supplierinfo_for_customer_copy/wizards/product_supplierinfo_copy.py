# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, _


class WizProductSupplierinfoCopy(models.TransientModel):
    _name = 'wiz.product.supplierinfo.copy'
    _description = 'Wizard to copy product supplier info.'

    name = fields.Char(
        string='Empty')
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        domain=[('customer', '=', True)],
        required=True)
    line_ids = fields.One2many(
        comodel_name='wiz.product.supplierinfo.copy.line',
        inverse_name='wiz_id',
        string='Lines')

    @api.model
    def default_get(self, fields):
        res = super(WizProductSupplierinfoCopy, self).default_get(fields)
        if 'line_ids' not in res:
            res['line_ids'] = []
        product_supplierinfos = self.env['product.supplierinfo'].browse(
            self.env.context.get('active_ids', []))
        for product_supplierinfo in product_supplierinfos:
            pricelist_values = []
            for pricelist in product_supplierinfo.pricelist_ids:
                pricelist_values.append((0, 0, {
                    'min_qty': pricelist.min_quantity,
                    'price': pricelist.price}))
            line = {
                'wiz_id': self.id,
                'partner_id': product_supplierinfo.name.id,
                'product_tmpl_id': product_supplierinfo.product_tmpl_id.id,
                'sequence': product_supplierinfo.sequence,
                'product_name': product_supplierinfo.product_name,
                'product_code': product_supplierinfo.product_code,
                'min_qty': product_supplierinfo.min_qty,
                'delay': product_supplierinfo.delay,
                'pricelist_ids': pricelist_values}
            res['line_ids'].append((0, 0, line))
        return res

    @api.multi
    def button_accept(self):
        self.ensure_one()
        product_supplierinfo_obj = self.env['product.supplierinfo']
        pricelist_partnerinfo_obj = self.env['pricelist.partnerinfo']
        pricelists = []
        for line in self.line_ids:
            product_exists = product_supplierinfo_obj.search([
                ('type', '=', 'customer'),
                ('name', '=', self.partner_id.id),
                ('product_tmpl_id', '=', line.product_tmpl_id.id)])
            if product_exists:
                continue
            product_supplierinfo = product_supplierinfo_obj.create({
                'type': 'customer',
                'name': self.partner_id.id,
                'product_tmpl_id': line.product_tmpl_id.id,
                'sequence': line.sequence,
                'product_name': line.product_name,
                'product_code': line.product_code,
                'min_qty': line.min_qty,
                'delay': line.delay})
            for pricelist in line.pricelist_ids:
                pricelists.append(pricelist_partnerinfo_obj.create({
                    'suppinfo_id': product_supplierinfo.id,
                    'product_tmpl_id': line.product_tmpl_id.id,
                    'min_quantity': pricelist.min_qty,
                    'price': pricelist.price}))
        view = self.env['ir.model.data'].get_object_reference(
            'product_supplierinfo_for_customer_copy',
            'wiz_product_supplierinfo_copy_wizard_end')
        view_id = view and view[1] or False
        return {
            'name': _('Product supplierinfo for customer created'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wiz.product.supplierinfo.copy',
            'view_id': view_id,
            'target': 'new',
            'views': False,
            'type': 'ir.actions.act_window'}


class WizProductSupplierinfoCopyLine(models.TransientModel):
    _name = 'wiz.product.supplierinfo.copy.line'
    _description = 'Wizard lines.'

    name = fields.Char(
        string='Empty')
    wiz_id = fields.Many2one(
        comodel_name='wiz.product.supplierinfo.copy',
        string='Wizard')
    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Product template',
        required=True)
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        domain=[('customer', '=', True)])
    sequence = fields.Integer(
        string='Sequence')
    product_name = fields.Char(
        string='Product name')
    product_code = fields.Char(
        string='Product code')
    min_qty = fields.Float(
        string='Min qty',
        required=True)
    delay = fields.Integer(
        string='Delay',
        required=True)
    pricelist_ids = fields.One2many(
        comodel_name='wiz.product.supplierinfo.copy.line.pricelist',
        inverse_name='wiz_line_id',
        string='Pricelist lines')


class WizProductSupplierinfoCopyLinePricelist(models.TransientModel):
    _name = 'wiz.product.supplierinfo.copy.line.pricelist'
    _description = 'Wizard pricelist lines.'

    name = fields.Char(
        string='Empty')
    wiz_line_id = fields.Many2one(
        comodel_name='wiz.product.supplierinfo.copy.line',
        string='Wizard line')
    min_qty = fields.Float(
        string='Min qty')
    price = fields.Float(
        string='Price')
