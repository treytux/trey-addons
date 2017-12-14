# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api, fields, _, exceptions
import logging
_log = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    invoice_line_desc = fields.Char(
        string='Invoice line description grouped')

    @api.constrains('invoice_line_desc')
    @api.one
    def _check_invoice_line_desc(self):
        '''It is not allowed to duplicate the same concept if the lines have
        different taxes.'''
        exists = {}
        for line in self.order_id.order_line:
            key = line.invoice_line_desc or line
            if key in exists and exists[key] != line.tax_id.ids:
                raise exceptions.ValidationError(
                    _('It is not allowed to duplicate the same concept if '
                        'the lines have different taxes.'))
            else:
                exists[key] = line.tax_id.ids


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def create_grouped_lines(self, order, invoice):
        '''Create invoice lines grouped by the description defined in the order
        lines associated sale.'''
        def _get_account(order_line):
            prop = self.env['ir.property'].get(
                'property_account_income_categ',
                'product.category')
            prop_id = prop and prop.id or False
            account_id = (
                order_line.order_id.fiscal_position and
                order_line.order_id.fiscal_position.map_account(prop_id) or
                prop_id)
            if not account_id:
                raise exceptions.Warning(_(
                    'Configuration Error! There is no income account '
                    'defined as global property.'))
            return account_id

        assert order.exists(), 'Param order is required!'
        lines = {}
        for order_line in order.order_line:
            key = order_line.invoice_line_desc or order_line
            if key not in lines:
                lines[key] = []
            lines[key].append(order_line)

        for key, olines in lines.iteritems():
            order_line = olines[0]
            data = {
                'name': order_line.name,
                'price_unit': order_line.price_unit,
                'quantity': order_line.product_uom_qty,
                'discount': order_line.discount,
                'invoice_id': invoice.id,
                'origin': order_line.order_id.name,
                'account_id': _get_account(order_line),
                'uos_id': (
                    order_line.product_uos and
                    order_line.product_uos.id or None),
                'product_id': (
                    order_line.product_id and
                    order_line.product_id.id or None),
                'invoice_line_tax_id': [
                    (4, t.id) for t in order_line.tax_id],
                'account_analytic_id': (
                    order_line.order_id.project_id and
                    order_line.order_id.project_id.id or False)}
            # Si hay mas de una linea agrupada, se modifica la linea
            if len(olines) > 1:
                data.update({
                    'name': order_line.invoice_line_desc,
                    # Hay que sumar el subtotal para tener en cuenta el numero
                    # de unidades
                    'price_unit': sum([l.price_subtotal for l in olines]),
                    'quantity': 1})
            self.env['account.invoice.line'].create(data)

    @api.model
    def _make_invoice(self, order, lines):
        '''Inherit _make_invoice to delete the lines of the invoice and create
        them again grouped.'''
        inv_id = super(SaleOrder, self)._make_invoice(order, lines)
        invoice = self.env['account.invoice'].browse(inv_id)
        for line in invoice.invoice_line:
            line.unlink()
        self.create_grouped_lines(order, invoice)
        # preinv tiene que contener todas las facturas del pedido menos la que
        # acabamos de crear
        preinvoices = order.invoice_ids - invoice
        for preinv in preinvoices:
            if preinv.state not in ('cancel',):
                for preline in preinv.invoice_line:
                    inv_line_id = preline.copy({
                        'invoice_id': inv_id,
                        'price_unit': -preline.price_unit})
                    lines.append(inv_line_id)
        invoice.button_compute()
        return inv_id
