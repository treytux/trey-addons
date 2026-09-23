###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockPickingInvoiceCarrier(models.TransientModel):
    _name = 'stock.picking.invoice_carrier'
    _description = 'Stock picking invoice carrier'

    line_ids = fields.One2many(
        comodel_name='stock.picking.invoice_carrier.line',
        inverse_name='wizard_id',
        string='Lines',
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if 'line_ids' not in res:
            res['line_ids'] = []
        pickings = self.env['stock.picking'].browse(
            self.env.context.get('active_ids', []))
        lines = self.env['stock.picking.invoice_carrier.line']
        for picking in pickings:
            line_data = {
                'wizard_id': self.id,
                'picking_id': picking.id,
                'carrier_id': picking.carrier_id.id,
            }
            lines |= lines.create(line_data)
        res.update({
            'line_ids': [(6, 0, lines.ids)],
        })
        return res

    def button_accept(self):
        invoices = {}
        for line in self.line_ids:
            if not line.picking_id.carrier_id or (
                    line.picking_id.invoice_carrier_id):
                continue
            if not line.picking_id.carrier_id.partner_id:
                raise ValidationError(
                    _('Carrier [%s] must have an assigned partner.')
                    % line.picking_id.carrier_id.name)
            carrier_partner = line.picking_id.carrier_id.partner_id
            if carrier_partner not in invoices:
                invoices[carrier_partner] = []
            invoices[carrier_partner].append(line.picking_id)
        created_invoices = []
        for carrier_partner, pickings in invoices.items():
            invoice_vals = {
                'type': 'in_invoice',
                'partner_id': carrier_partner.id,
                'origin': ', '.join([p.name for p in pickings]),
                'invoice_line_ids': [],
            }
            for picking in pickings:
                product = picking.carrier_id.product_id
                line_vals = {
                    'name': _('Picking %s') % picking.name,
                    'product_id': picking.carrier_id.product_id.id,
                    'price_unit': picking.carrier_id.product_id.standard_price,
                    'quantity': 1,
                    'picking_id': picking.id,
                    'account_id': product.property_account_expense_id or (
                        product.categ_id.property_account_expense_categ_id.id
                    ),
                }
                invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
            invoice = self.env['account.invoice'].create(invoice_vals)
            for picking in pickings:
                picking.invoice_carrier_id = invoice.id
            created_invoices.append(invoice)
        return created_invoices


class StockPickingInvoiceCarrierLine(models.TransientModel):
    _name = 'stock.picking.invoice_carrier.line'
    _description = 'Wizard lines'

    wizard_id = fields.Many2one(
        comodel_name='stock.picking.invoice_carrier',
        string='Wizard',
    )
    picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Picking',
    )
    carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string='Carrier',
    )
