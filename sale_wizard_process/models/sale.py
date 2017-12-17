# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, exceptions, _
import openerp.addons.decimal_precision as dp
from datetime import date
import logging
_log = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _prepare_order_line_procurement(self, order, line, group_id=False):
        res = super(SaleOrder, self)._prepare_order_line_procurement(
            order, line, group_id)
        res['gross_measures'] = line.gross_measures
        return res

    @api.multi
    def process_order(self):
        '''Confirm sale order, create picking and transfer it (if products are
        stockable or consumable) and create invoice.
        '''
        def run_create_invoice(self, pick):
            inv_wizard = self.env['stock.invoice.onshipping'].with_context(
                active_ids=[pick.id]).create({
                    'invoice_date': date.today().strftime('%Y-%m-%d')})
            return inv_wizard.with_context(
                active_ids=[pick.id]).create_invoice()

        sol = {}
        for l in self.order_line:
            if l.product_id not in sol:
                sol[l.product_id] = []
            sol[l.product_id].append({
                'qty': l.product_uom_qty,
                'lot': l.lot_id})
        self.action_button_confirm()
        if len(self.picking_ids) > 1:
            raise exceptions.Warning(_(
                'This order has generated more than one stock picking. You '
                'must confirmed them manually.'))
        if self.picking_ids.exists():
            for pick in self.picking_ids:
                # Check to avoid creating a picking without some of the
                # product moves due to the do_prepare_partial function
                for move in pick.move_lines:
                    if move.product_qty != move.product_uom_qty:
                        raise exceptions.Warning(_(
                            'The quantity of the product and the quantity of '
                            'the unit of product of the product %s are '
                            'different. Review rounding of units of measure '
                            'or try confirm it manually.') %
                            move.product_id.name)
                pick.force_assign()
                pick_wizard = self.env['stock.transfer_details'].with_context(
                    active_model='stock.picking',
                    active_ids=[pick.id],
                    active_id=len([pick.id]) and pick.id or False).create({
                        'picking_id': pick.id})
                items = {}
                for item in pick_wizard.item_ids:
                    if item.product_id not in items:
                        items[item.product_id] = []
                    items[item.product_id].append({
                        'qty': item.quantity,
                        'item': item})
                to_split = {}
                for sol_product, sol_values in sol.iteritems():
                    for it_product, it_values in items.iteritems():
                        if it_product == sol_product:
                            for sol_val in sol_values:
                                if (len(it_values) > 0 and
                                        it_values[0]['qty'] != sol_val['qty']):
                                    if it_values[0]['item'] not in to_split:
                                        to_split[it_values[0]['item']] = []
                                    to_split[it_values[0]['item']].append({
                                        'qty': sol_val['qty'],
                                        'lot': sol_val['lot']})
                                else:
                                    it_values[0]['item'].write({
                                        'quantity': sol_val['qty'],
                                        'lot_id': (
                                            sol_val['lot'] and
                                            sol_val['lot'].id or None)})
                for it, it_values in to_split.iteritems():
                    count = 0
                    for i in range(len(it_values) - 1):
                        it.split_quantities()
                    for item in pick_wizard.item_ids:
                        if item.product_id == it.product_id:
                            item.write({
                                'quantity': it_values[count]['qty'],
                                'lot_id': (
                                    it_values[count]['lot'] and
                                    it_values[count]['lot'].id or None)})
                            count += 1
                pick_wizard.with_context(
                    active_model='stock.picking',
                    active_ids=[pick.id],
                    active_id=len(
                        [pick.id]) and pick.id or False).do_detailed_transfer()
                pick.action_done()
                pick.invoice_state = '2binvoiced'
                run_create_invoice(self, pick)
        else:
            wizard = self.env['sale.advance.payment.inv'].with_context({
                'active_ids': [self.id],
                'active_model': 'sale.order',
                'active_id': self.id}).create(
                    {'advance_payment_method': 'all'})
            wizard.create_invoices()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    lot_id = fields.Many2one(
        comodel_name='stock.production.lot',
        string='Lot')
    qty_per_pallet = fields.Float(
        string='Quantity per pallet',
        default=1)
    pallet_qty = fields.Integer(
        string='Pallets number',
        default=1)
    m2 = fields.Float(
        string='m2',
        compute='_compute_m2_m3',
        digits=dp.get_precision('Product UoS'))
    m3 = fields.Float(
        string='m3',
        compute='_compute_m2_m3',
        digits=dp.get_precision('Product UoS'))
    gross_measures = fields.Char(
        string='Gross measures')

    @api.multi
    @api.depends(
        'product_id', 'product_uom_qty', 'qty_per_pallet', 'pallet_qty')
    def _compute_m2_m3(self):
        for line in self:
            if not line.product_id.exists():
                return 0
            line.m2 = line.product_uos_qty
            line.m3 = line.m2 * line.product_id.width or 1

    @api.onchange('qty_per_pallet', 'pallet_qty')
    def onchange_qty_per_pallet_pallet_qty(self):
        self.product_uom_qty = self.qty_per_pallet * self.pallet_qty
