# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, _
import logging
_log = logging.getLogger(__name__)


class StockLocationInvoice(models.TransientModel):
    _name = 'stock.location.invoice'

    @api.model
    def _default_lines(self):
        location_id = self.env.context.get('active_id')
        quants = self.env['stock.quant'].search(
            [('location_id', 'child_of', location_id)])
        products = {}
        for quant in quants:
            products.setdefault(quant.product_id.id, []).append(quant)
        lines = []
        for product_id, quants in products.iteritems():
            qty = sum([q.qty for q in quants])
            if qty <= 0:
                continue
            lines.append((0, 0, {
                'product_id': product_id,
                'quant_ids': [(6, 0, [q.id for q in quants])],
                'qty': 0,
                'stock_qty': qty}))
        return lines

    @api.model
    def _default_journal(self):
        journals = self.env['account.journal'].search([('type', '=', 'sale')])
        return journals and journals[0] or False

    @api.model
    def _default_partner(self):
        location_id = self.env.context.get('active_id')
        location = self.env['stock.location'].browse(location_id)
        if location.partner_id:
            return location.partner_id.id
        quants = self.env['stock.quant'].search(
            [('location_id', 'child_of', location_id)])
        for quant in quants:
            if not quant.history_ids:
                continue
            for move in quant.history_ids:
                if move.partner_id:
                    return move.partner_id.id
                elif move.picking_id and move.picking_id.partner_id:
                    return move.picking_id.partner_id.id
        return False

    ref = fields.Char(
        string='Partner ref')
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location',
        default=lambda self: self.env.context.get('active_id'))
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        default=_default_partner,
        string='Partner')
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        domain='[("type", "=", "sale")]',
        default=_default_journal,
        string='Journal')
    line_ids = fields.One2many(
        comodel_name='stock.location.invoice.line',
        inverse_name='wizard_id',
        string='Lines',
        default=_default_lines)
    total_qty = fields.Float(
        string='Total',
        compute='compute_total_qty')
    one_line = fields.Boolean(
        string='One line')
    one_line_concept = fields.Char(
        string='Concept')

    @api.one
    @api.depends('line_ids')
    def compute_total_qty(self):
        self.total_qty = sum([l.qty for l in self.line_ids])

    @api.multi
    def refresh_view(self):
        view = self.env.ref(
            'stock_location_invoice.stock_location_invoice_wizard')
        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'view_id': view.id,
            'type': 'ir.actions.act_window',
            'target': 'new'}

    @api.multi
    def action_qty_all(self):
        self.ensure_one()
        for line in self.line_ids:
            line.qty = line.stock_qty
        return self.refresh_view()

    @api.multi
    def action_qty_zero(self):
        self.ensure_one()
        for line in self.line_ids:
            line.qty = 0
        return self.refresh_view()

    @api.one
    def button_accept(self):
        picking = self.create_picking()
        invoice_ids = picking.action_invoice_create(
            journal_id=self.journal_id.id,
            group=True,
            type='out_invoice')
        assert len(invoice_ids) == 1, _(
            'More that an invoice created, programming error!!')
        invoice = self.env['account.invoice'].browse(invoice_ids[0])
        for line in invoice.invoice_line:
            data = self.env['account.invoice.line'].product_id_change(
                line.product_id.id, line.uos_id.id, qty=line.quantity,
                name=line.name, partner_id=line.invoice_id.partner_id.id)
            line.write({
                'price_unit': data['value']['price_unit'],
                'discount': data['value'].get('discount')})
        invoice.partner_id = invoice.partner_id.commercial_partner_id.id
        return invoice.id

    @api.multi
    def create_picking(self):
        wh_id = self.env['stock.location'].get_warehouse(self.location_id)
        warehouse = self.env['stock.warehouse'].browse(wh_id)
        location_dest = warehouse.out_type_id.default_location_dest_id
        picking = self.env['stock.picking'].create({
            'client_reference': self.ref,
            'partner_id': self.partner_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': location_dest.id,
            'picking_type_id': warehouse.out_type_id.id,
            'invoice_state': '2binvoiced',
            'origin': _('Inv. location %s') % self.location_id.display_name})
        for line in self.line_ids:
            if not line.qty:
                continue
            res = self.env['stock.move'].onchange_product_id(
                prod_id=line.product_id.id, loc_id=self.location_id.id,
                loc_dest_id=location_dest.id, partner_id=self.partner_id.id)
            res['value'].update({
                'product_id': line.product_id.id,
                'product_uom_qty': line.qty,
                'invoice_state': '2binvoiced',
                'picking_id': picking.id})
            self.env['stock.move'].create(res['value'])
        picking.action_confirm()
        picking.action_assign()
        picking.action_done()
        picking.client_reference = self.ref
        return picking


class StockLocationInvoiceLine(models.TransientModel):
    _name = 'stock.location.invoice.line'

    wizard_id = fields.Many2one(
        comodel_name='stock.location.invoice',
        string='Stock location invoice')
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product')
    quant_ids = fields.Many2many(
        comodel_name='stock.quant',
        relation='stock_location_invoice_line2quant_rel',
        column1='line_id',
        column2='quant_id')
    qty = fields.Float(
        string='Quantity')
    stock_qty = fields.Float(
        string='Stock quantity')
