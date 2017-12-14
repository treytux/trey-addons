# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, exceptions, _
import logging
_log = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    gift_ids = fields.One2many(
        comodel_name='sale.order.gift',
        inverse_name='order_id',
        string='Gifts',
        copy=False,
        readonly=True,
        states={'draft': [('readonly', False)]})
    gift_quantity = fields.Float(
        string='Gift Quantity',
        compute='compute_gift_quantity',
        store=True,
        readonly=True,
        copy=False)
    gift_max_quantity = fields.Float(
        string='Max Quantity',
        compute='compute_gift_quantity',
        store=True,
        readonly=True,
        copy=False)

    @api.one
    @api.depends('gift_ids')
    def compute_gift_quantity(self):
        if self.gift_ids:
            self.gift_quantity = sum([g.quantity for g in self.gift_ids])
            # Como todas las lineas tienen guardado el maximo, coger una
            # cualquiera
            if self.gift_ids.exists():
                self.gift_max_quantity = self.gift_ids[0].max_total
        else:
            self.quantity = 0
            self.max_quantity = 0

    @api.multi
    def get_promolines(self):
        if not self.pricelist_id:
            return []
        version = self.pricelist_id.get_version()
        if not version:
            return []
        # Agrupar todos los productos de las lineas en la misma unidad de venta
        products = {l.product_id.id: 0
                    for l in self.order_line if l.product_id}
        for line in self.order_line:
            if line.product_id:
                products[line.product_id.id] += line.get_qty_uom_reference()
        # Buscar por producto la tarifa que le corresponde
        promo_lines = [p._get_gifts(products) for p in version.promotion_ids]
        return [p for p in promo_lines if p]

    @api.multi
    def _apply_promotion_price(self, promo_lines):
        self.ensure_one()
        for promo_line in promo_lines:
            for line in self.order_line:
                line.price_unit = line.promotion_get_price(promo_line)

    @api.multi
    def _apply_promotion_gifts(self, promo_lines):
        self.ensure_one()
        qtys = {'%s:%s' % (g.product_id.id, g.uom_id.id): g.quantity
                for g in self.gift_ids}
        lines = {}
        max_total = 0
        sequence = 0
        for line in promo_lines:
            count_max_total = False
            sequence += 1
            # Rellenar productos de regalo
            for product in line.promotion_id.optional_product_ids:
                key = '%s:%s' % (product.id, line.gift_uom_id.id)
                qty = key in qtys and qtys[key] or 0
                if key in lines:
                    li = lines[key]
                    max_qty = li['max_quantity'] + line.gift_quantity
                    if not count_max_total:
                        max_total += max_qty
                        count_max_total = True
                    lines[key].update({
                        'quantity': qty > max_qty and max_qty or qty,
                        'max_quantity': max_qty,
                        'sequence': sequence,
                        'promotion_line_ids': [
                            (6, 0,
                             li['promotion_line_ids'][0][2] + [line.id])]})
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
                        'promotion_line_ids': [(6, 0, [line.id])],
                        'uom_id': line.gift_uom_id.id}
        # Escribir en todas las lineas el max_qty (suma de todas)
        [v.update({'max_total': max_total}) for k, v in lines.iteritems()]
        self.gift_ids = (
            [(6, 0, [])] + [(0, 0, v) for k, v in lines.iteritems()])

    @api.onchange('order_line')
    def update_gifts(self):
        promo_lines = self.get_promolines()
        self._apply_promotion_price(promo_lines)
        self._apply_promotion_gifts(promo_lines)

    @api.one
    @api.constrains('gift_ids')
    def _check_gift_ids(self):
        '''Check:
            - The number of gifts does not exceed the maximum amount
            and
            - The sum of the amounts of the same sequence does not exceed the
            maximum of the lines of this sequence (because it is the same for
            all of them).
        '''
        if self.gift_quantity > self.gift_max_quantity:
            raise exceptions.Warning(_(
                'You have exceeded the maximum number of gifts. You are '
                'trying give it {0}, but the maximum is {1}.').format(
                    self.gift_quantity, self.gift_max_quantity))
        sum_gift = {}
        for gift in self.gift_ids:
            if gift.sequence not in sum_gift:
                sum_gift[gift.sequence] = 0
            sum_gift[gift.sequence] += gift.quantity
            if sum_gift[gift.sequence] > gift.max_quantity:
                raise exceptions.Warning(_(
                    'The sum of the amounts of gift lines ({0}) has exceeded '
                    'the maximum quantity: ({1}).').format(
                        sum_gift[gift.sequence], gift.max_quantity))

    @api.multi
    def create_gifts(self):
        self.ensure_one()
        linetax = None
        for line in self.order_line:
            if line.gift_origin_id:
                line.unlink()
            if line.tax_id:
                linetax = [(6, 0, [t.id for t in line.tax_id])]

        for line in self.gift_ids:
            if line.quantity > 0:
                self.env['sale.order.line'].create({
                    'order_id': self.id,
                    'product_id': line.product_id.id,
                    'product_uom': line.uom_id.id,
                    'product_uom_qty': line.quantity,
                    'tax_id': linetax,
                    'price_unit': 0,
                    'discount': 0,
                    'gift_origin_id': line.id})

    @api.one
    def action_button_confirm(self):
        self.create_gifts()
        return super(SaleOrder, self).action_button_confirm()

    @api.multi
    def button_dummy(self):
        '''Inherit function to allow update promotions and gifts.'''
        super(SaleOrder, self).button_dummy()
        self.update_gifts()
        return True


class SaleOrderGift(models.Model):
    _name = 'sale.order.gift'
    _description = 'Sale Order Gift'

    order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Order',
        delete='cascade')
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        readonly=True)
    uom_id = fields.Many2one(
        comodel_name='product.uom',
        string='UoM',
        required=True)
    quantity = fields.Float(
        string='Quantity')
    max_quantity = fields.Float(
        string='Maximum quantity')
    max_total = fields.Float(
        string='Maximum total')
    sequence = fields.Integer(
        string='Sequence')
    promotion_line_ids = fields.Many2many(
        comodel_name='product.promotion.line',
        relation='saleorder2productpromotionline_rel',
        column1='gift_id',
        column2='promotion_line_id')

    @api.onchange('quantity', 'max_quantity')
    def set_quantity(self):
        if self.quantity > self.max_quantity:
            self.quantity = self.max_quantity
        elif self.quantity < 0:
            raise exceptions.Warning(_(
                'Negative amounts are not allowed.'))


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    gift_origin_id = fields.Many2one(
        comodel_name='sale.order.gift',
        string='Gift',
        readonly=True)

    @api.multi
    def get_qty_uom_reference(self):
        '''Return qty in uom reference of this category.'''
        self.ensure_one()
        if not self.product_id.exists():
            return self.product_uom_qty
        uom_obj = self.env['product.uom']
        product_uom = uom_obj.search([
            ('category_id', '=', self.product_uom.category_id.id),
            ('uom_type', '=', 'reference')])
        return uom_obj._compute_qty_obj(
            self.product_uom, self.product_uom_qty, product_uom)

    @api.multi
    def promotion_get_price(self, promoline):
        self.ensure_one()
        if self.product_id not in promoline.promotion_id.product_ids:
            return self.price_unit
        uom_qty = self.product_uom._compute_qty_obj(
            promoline.uom_id, promoline.quantity, self.product_uom)
        return promoline.price / uom_qty

    @api.multi
    def product_id_change(self, pricelist, product, qty=0,
                          uom=False, qty_uos=0, uos=False, name='',
                          partner_id=False, lang=False, update_tax=True,
                          date_order=False, packaging=False,
                          fiscal_position=False, flag=False):
        res = super(SaleOrderLine, self).product_id_change(
            pricelist, product, qty=qty, uom=uom, qty_uos=qty_uos, uos=uos,
            name=name, partner_id=partner_id, lang=lang, update_tax=update_tax,
            date_order=date_order, packaging=packaging,
            fiscal_position=fiscal_position, flag=flag)
        promolines = self.order_id.get_promolines()
        for promoline in promolines:
            res['value']['price_unit'] = self.promotion_get_price(promoline)
        return res

    @api.multi
    def product_uom_change(self, pricelist, product, qty=0, uom=False,
                           qty_uos=0, uos=False, name='', partner_id=False,
                           lang=False, update_tax=True, date_order=False):
        res = super(SaleOrderLine, self).product_uom_change(
            pricelist, product, qty=qty, uom=uom, qty_uos=qty_uos, uos=uos,
            name=name, partner_id=partner_id, lang=lang,
            update_tax=update_tax, date_order=date_order)

        promolines = self.order_id.get_promolines()
        for promoline in promolines:
            res['value']['price_unit'] = self.promotion_get_price(promoline)

        return res
