###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_return = fields.Boolean(
        string='Is Return',
    )
    state_return = fields.Selection([
        ('draft', 'Draft Return'),
        ('sent', 'Sent Return'),
        ('sale', 'Sale Return'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')],
        string='Sale Return Status',
        compute='_compute_state_return',
    )

    @api.one
    @api.depends('state')
    def _compute_state_return(self):
        self.state_return = self.state

    @api.model
    def create(self, vals):
        if vals.get('is_return') and 'name' not in vals:
            vals['name'] = self.env['ir.sequence'].next_by_code('sale.return')
        return super().create(vals)

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        def recompute_origin(invoice):
            sale_names = list(set(
                s.order_id.name
                for i in invoice.invoice_line_ids
                for s in i.sale_line_ids))
            invoice.origin = ', '.join(sale_names)

        invoice_ids = super().action_invoice_create(grouped, final)
        for invoice in self.env['account.invoice'].browse(invoice_ids):
            if invoice.amount_total != 0:
                continue
            new_invoice = invoice.copy({
                'type': 'out_refund',
                'invoice_line_ids': False})
            for line in invoice.invoice_line_ids:
                if line.quantity > 0:
                    continue
                line.write({
                    'invoice_id': new_invoice.id,
                    'quantity': line.quantity * -1})
            for invoice in [new_invoice, invoice]:
                recompute_origin(invoice)
                invoice.compute_taxes()
            if new_invoice.amount_total == 0:
                new_invoice.unlink()
            else:
                invoice_ids.append(new_invoice.id)
        return invoice_ids

    @api.multi
    def _get_tax_amount_by_group(self):
        self.ensure_one()
        if not self.is_return:
            return super()._get_tax_amount_by_group()
        res = {}
        for line in self.order_line:
            price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
            qty = (line.product_uom_qty * -1) + line.qty_change
            taxes = line.tax_id.compute_all(
                price_reduce, quantity=qty,
                product=line.product_id,
                partner=self.partner_shipping_id)['taxes']
            for tax in line.tax_id:
                group = tax.tax_group_id
                res.setdefault(group, {'amount': 0.0, 'base': 0.0})
                for t in taxes:
                    tax_ids = tax.children_tax_ids.ids
                    if t['id'] == tax.id or t['id'] in tax_ids:
                        res[group]['amount'] += t['amount']
                        res[group]['base'] += t['base']
        res = sorted(res.items(), key=lambda l: l[0].sequence)
        res = [
            (l[0].name, l[1]['amount'], l[1]['base'], len(res)) for l in res]
        return res
