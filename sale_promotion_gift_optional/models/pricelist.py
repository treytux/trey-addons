# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, exceptions, _
import openerp.addons.decimal_precision as dp


class PricelistVersion(models.Model):
    _inherit = 'product.pricelist.version'

    promotion_ids = fields.One2many(
        comodel_name='product.promotion',
        inverse_name='version_id',
        string='Promotions')


class Promotion(models.Model):
    _name = 'product.promotion'
    _description = 'Promotion'
    _order = 'sequence'

    name = fields.Char(
        string='Name',
        required=True)
    sequence = fields.Integer(
        string='Sequence')
    version_id = fields.Many2one(
        comodel_name='product.pricelist.version',
        string='Pricelist Version',
        required=True)
    product_ids = fields.Many2many(
        comodel_name='product.product',
        relation='product_promotion_product_rel',
        domain=[('sale_ok', '=', True)],
        column1='promotion_id',
        column2='product_id')
    optional_product_ids = fields.Many2many(
        comodel_name='product.product',
        relation='product_promotion_optional_product_rel',
        column1='promotion_id',
        column2='product_id')
    line_ids = fields.One2many(
        comodel_name='product.promotion.line',
        inverse_name='promotion_id',
        string='Lines')

    @api.multi
    def _get_gifts(self, products):
        '''
            Get promotion line
            @params products is a dict {product_id: qty, product_id: qty, ...}
        '''
        self.ensure_one()

        def get_qty_uom_reference(from_uom, qty):
            uom_ref = from_uom.search([
                ('category_id', '=', from_uom.category_id.id),
                ('uom_type', '=', 'reference')])
            return from_uom._compute_qty_obj(from_uom, qty, uom_ref[0])

        total = sum([products[p.id]
                     for p in self.product_ids
                     if p.id in products])
        for line in self.line_ids:
            qty = get_qty_uom_reference(line.uom_id, line.quantity)
            if total >= qty:
                return line
        return None

    @api.constrains('line_ids')
    @api.one
    def _check_uom_category(self):
        '''By each line, the measurement units must belong to the same
        category.'''
        uom_categ_ids = []
        if self.line_ids.exists():
            uom_categ_ids = [line.uom_id.id for line in self.line_ids]
        if len(list(set(uom_categ_ids))) > 1:
            raise exceptions.ValidationError(
                _('The units of the lines must belong to the same '
                    'category.'))

    @api.multi
    def copy(self, default):
        '''When copy, lines must be copied.'''
        if default is None:
            default = {}
        default['name'] = _("%s (copy)") % (self.name)
        lines = []
        for line in self.line_ids:
            line_data = {
                'sequence': line.sequence,
                'quantity': line.quantity,
                'uom_id': line.uom_id.id,
                'gift_quantity': line.gift_quantity,
                'gift_uom_id': line.gift_uom_id.id,
                'price': line.price}
            lines.append((0, 0, line_data))
            default.update({'line_ids': lines})
        return super(Promotion, self).copy(default)


class PromotionLine(models.Model):
    _name = 'product.promotion.line'
    _description = 'Promotion Line'
    _order = 'sequence'

    name = fields.Char(
        string='Name')
    promotion_id = fields.Many2one(
        comodel_name='product.promotion',
        string='Promotion')
    sequence = fields.Integer(
        string='Sequence')
    quantity = fields.Float(
        string='Quantity')
    uom_id = fields.Many2one(
        comodel_name='product.uom',
        string='UoM',
        required=True)
    gift_quantity = fields.Float(
        string='Gift Qty')
    gift_uom_id = fields.Many2one(
        comodel_name='product.uom',
        string='Gift UoM',
        required=True)
    price = fields.Float(
        string='Price by UoM',
        digits=dp.get_precision('Product Price'),
        required=True)


class Pricelist(models.Model):
    _inherit = 'product.pricelist'

    @api.multi
    def get_version(self, date=None):
        date = fields.Date.from_string(date or fields.Date.today())
        version = None
        version_obj = self.env['product.pricelist.version']
        for v in self.version_id:
            if ((v.date_start is False) or
                (fields.Date.from_string(v.date_start) <= date)) \
                and ((v.date_end is False) or
                     (fields.Date.from_string(v.date_end) >= date)):
                return v
        version = version_obj.search([
            ('pricelist_id', '=', self.id), ('active', '=', True)],
            order='id desc')
        if not version:
            raise exceptions.Warning(_(
                'Current pricelist has no active version!\nPlease create or '
                'activate one.'))
        return None

    @api.model
    def apply_pricelist(self, partner_id, uom_qtys):
        partner = self.env['res.partner'].sudo().browse(partner_id)
        return partner.property_product_pricelist._apply_pricelist(
            uom_qtys, partner_id=partner.id)

    @api.multi
    def _apply_pricelist(self, uom_qtys, partner_id=None):
        '''
        uom_qtys = {
            product_id: {
                uom_id: qty
                uom_id: qty
            }
        }
        '''
        self.ensure_one()

        if not partner_id:
            partner_id = self.env.user.partner_id.id

        # Normalizar los datos pasados
        aux = {}
        for pid, v in uom_qtys.iteritems():
            pid = int(pid)
            aux[pid] = {}
            for uomid, qty in v.iteritems():
                try:
                    qty = float(qty)
                except:
                    continue
                aux[pid][int(uomid)] = qty
        uom_qtys = aux

        def get_qty_uom_reference(uom_id, qty):
            uom = self.env['product.uom'].browse(uom_id)
            uom_reference = self.env['product.uom'].search([
                ('category_id', '=', uom.category_id.id),
                ('uom_type', '=', 'reference')])
            return uom_reference._compute_qty_obj(
                uom, qty, uom_reference[0])

        version = self.get_version()
        product_qtys = {pid: 0 for pid in uom_qtys.keys()}
        for product_id, uoms in uom_qtys.iteritems():
            for uom_id, qty in uoms.iteritems():
                product_qtys[product_id] += get_qty_uom_reference(uom_id, qty)

        # Buscar por producto la tarifa que le corresponde
        promo_lines = [p._get_gifts(product_qtys)
                       for p in version.promotion_ids]
        promo_lines = [p for p in promo_lines if p]

        def promotion_get_price(product_id, qty, uom_id, promo_lines=None):
            if promo_lines is None:
                promo_lines = []
            uom = self.env['product.uom'].browse(uom_id)
            if promo_lines:
                promo_line = [p for p in promo_lines
                              if product_id in p.promotion_id.product_ids.ids]
                if promo_line:
                    uom_qty = uom._compute_qty_obj(
                        promo_line[0].uom_id, promo_line[0].quantity, uom)
                    return promo_line[0].price / uom_qty
            uom_qty = get_qty_uom_reference(uom_id, 1)
            price = self.price_get(
                product_id, (uom_qty * qty), partner_id)[self.id]
            return uom_qty * price

        res = {}
        for product_id, uoms in uom_qtys.iteritems():
            res[product_id] = {}
            for uom_id, qty in uoms.iteritems():
                res[product_id][uom_id] = promotion_get_price(
                    product_id, qty, uom_id, promo_lines)

        lines = {}
        sequence = 0
        max_total = 0
        for line in promo_lines:
            count_max_total = False
            sequence += 1
            # Rellenar productos de regalo
            for product in line.promotion_id.optional_product_ids:
                key = '%s:%s' % (product.id, line.gift_uom_id.id)
                if key in lines:
                    l = lines[key]
                    max_qty = l['max_quantity'] + line.gift_quantity
                    if not count_max_total:
                        max_total += max_qty
                        count_max_total = True
                    lines[key].update({
                        'quantity': qty > max_qty and max_qty or qty,
                        'max_quantity': max_qty,
                        'sequence': sequence,
                        'promotion_line_ids': (
                            l['promotion_line_ids'] +
                            [line.id, line.promotion_id.name])})
                else:
                    if not count_max_total:
                        max_total += line.gift_quantity
                        count_max_total = True
                    lines[key] = {
                        'product_id': product.id,
                        'quantity': (qty > line.gift_quantity and
                                     line.gift_quantity or qty),
                        'max_quantity': line.gift_quantity,
                        'sequence': sequence,
                        'promotion_line_ids': [line.id,
                                               line.promotion_id.name],
                        'uom_id': line.gift_uom_id.id}
        [v.update({'max_total': max_total}) for k, v in lines.iteritems()]
        res['gifts'] = lines
        return res
