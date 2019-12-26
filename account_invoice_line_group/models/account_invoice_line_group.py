###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################

from odoo import _, api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round


class AccountInvoiceLineGroup(models.Model):
    _name = 'account.invoice.line.group'

    name = fields.Char(
        string='Concept',
        required=True,
    )
    description = fields.Char(
        string='Description to Print',
        required=True,
    )
    quantity_method = fields.Selection(
        selection=[
            ('real', 'Real'),
            ('fixed', 'Fixed'),
            ('one', 'One'),
        ],
        string='Qty Method',
        default='one',
        required=True,
    )
    qty = fields.Float(
        digits=dp.get_precision('Product Unit of Measure'),
        default=1.0,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('assigned', 'Assigned'),
        ],
        compute='_compute_state',
        store=True,
    )
    invoice_line_ids = fields.One2many(
        comodel_name='account.invoice.line',
        inverse_name='group_id',
        string='Invoice Lines',
    )
    invoice_count = fields.Integer(
        string='Invoices',
        compute='_compute_invoice_line_ids',
    )

    @api.constrains("qty")
    def check_positive_val(self):
        for record in self:
            if record.qty <= 0:
                raise ValidationError(
                    _("Quantity value must be greater than 0.")
                )

    @api.depends('invoice_line_ids.invoice_id.state')
    def _compute_state(self):
        for record in self:
            if any(x.state in ['open', 'done'] for x in
                   record.mapped('invoice_line_ids.invoice_id')):
                record.state = 'assigned'
            else:
                record.state = 'draft'

    @api.depends('invoice_line_ids')
    def _compute_invoice_line_ids(self):
        for group in self:
            group.invoice_count = len(group.invoice_line_ids)

    def action_view_invoices(self):
        self.ensure_one()
        invoices = self.mapped('invoice_line_ids.invoice_id')
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.invoice_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view) for state, view in
                    action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def _get_data(self, invoice):
        self.ensure_one()
        precision = self.env['decimal.precision']
        data = {}
        if not invoice:
            return data
        lines = invoice.invoice_line_ids.filtered(lambda l: l.group_id == self)
        price_subtotal = sum(lines.mapped('price_subtotal'))
        if self.quantity_method == 'real':
            qty = sum(lines.mapped('quantity'))
        elif self.quantity_method == 'fixed':
            qty = self.qty
        elif self.quantity_method == 'one':
            qty = 1.0
        else:
            return data
        if qty:
            price_unit = float_round(lines.get_price_unit_by_line() / qty,
                                     precision_digits=precision.precision_get(
                                         'Product Price'))
            discount = (1 - (price_subtotal / (qty * price_unit))) * 100
            discount = float_round(
                discount, precision_digits=precision.precision_get(
                    'Product Price'))
        else:
            price_unit = 0.0
            discount = 0.0
        data.update({
            'qty': qty,
            'discount': round(discount, 2),
            'price_unit': round(price_unit, 2),
            'price_subtotal': price_subtotal,
        })
        return data
