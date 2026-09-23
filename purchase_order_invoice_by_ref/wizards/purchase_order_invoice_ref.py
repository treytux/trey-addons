###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.tools.float_utils import float_compare


class PurchaseOrderInvoiceRefs(models.TransientModel):
    _name = 'purchase.order.invoice_refs'
    _description = 'Purchase order invoice by refs'

    @api.model
    def _default_method(self):
        model = self.env['purchase.order.invoice']
        return model._fields['method'].default(model)

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True,
    )
    references = fields.Text(
        string='References',
        required=True,
    )
    method = fields.Selection(
        selection=[
            ('received', 'Invoice received not invoiced'),
            ('all-not-invoiced', 'Invoice all lines not invoiced'),
            ('all', 'Invoice all lines'),
        ],
        string='Invoice method',
        default=_default_method,
        required=True,
    )
    join_purchases = fields.Boolean(
        string='Join purchases same supplier',
        default=True,
    )
    line_ids = fields.One2many(
        comodel_name='purchase.order.invoice_ref.lines',
        inverse_name='wizard_id',
        string='Errors',
    )
    purchase_ids = fields.Many2many(
        comodel_name='purchase.order',
        relation='purchase_order2invoice_refs_rel',
        column1='invoice_ref_id',
        column2='purchase_id',
    )
    step = fields.Integer(
        string='Step',
    )

    def _reopen_view(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.ids[0],
            'res_model': self._name,
            'target': 'new',
            'context': {},
        }

    def _error(self, message, ref):
        self.ensure_one()
        self.line_ids.create({
            'wizard_id': self.id,
            'name': message,
            'ref': ref,
        })

    def _warning(self, message, ref):
        self.ensure_one()
        self.line_ids.create({
            'type': 'warning',
            'wizard_id': self.id,
            'name': message,
            'ref': ref,
        })

    def references_to_list(self):
        self.ensure_one()
        txt = self.references
        txt = txt.split('\n')
        txt = [t.strip() for t in txt]
        return [t for t in txt if t]

    def any_purchase_lines_to_invoice(self, purchase):
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        return any(float_compare(
            line.qty_invoiced, line.product_qty
            if line.product_id.purchase_method == 'purchase'
            else line.qty_received, precision_digits=precision) == -1
            for line in purchase.mapped('order_line'))

    def is_purchase_found(self, purchase, purchase_ids):
        lines_to_invoice = self.any_purchase_lines_to_invoice(purchase)
        return (
            len(purchase) == 1 and purchase.state in ['purchase', 'done']
            and purchase.id not in purchase_ids and not lines_to_invoice)

    def check_purchase_errors(self, purchases, purchase_ids, ref):
        errors = []
        warnings = []
        if len(purchases) > 1:
            errors.append((_('Return more than one purchase.'), ref))
            return errors, warnings
        if len(purchases) == 0:
            errors.append((_('Purchase not found.'), ref))
            return errors, warnings
        if purchases.state not in ['purchase', 'done']:
            errors.append((_(
                'Purchase in state %s, must be confirmed or done.') % (
                    purchases.state), ref))
            return errors, warnings
        if purchases.id in purchase_ids:
            warnings.append((_('Reference duplicate, ignore one.'), ref))
            return errors, warnings
        lines_to_invoice = self.any_purchase_lines_to_invoice(purchases)
        if not lines_to_invoice:
            warnings.append((_('Purchase already invoiced.'), ref))
            return errors, warnings
        return errors, warnings

    def search_by_reference(self, ref, purchase_ids):
        errors = []
        warnings = []
        purchases = self.purchase_ids.search([
            '|',
            ('partner_id', '=', self.partner_id.id),
            ('partner_id', 'child_of', self.partner_id.id),
            '|',
            ('name', '=', ref),
            ('partner_ref', '=', ref),
        ])
        if self.is_purchase_found(purchases, purchase_ids):
            return purchases, errors, warnings
        errors, warnings = self.check_purchase_errors(
            purchases, purchase_ids, ref)
        return purchases, errors, warnings

    def save_errors(self, errors, warnings):
        for error in errors:
            self._error(error[0], error[1])
        for warning in warnings:
            self._warning(warning[0], warning[1])

    def find_purchases(self):
        self.ensure_one()
        purchase_ids = []
        for ref in self.references_to_list():
            purchases, errors, warnings = self.search_by_reference(
                ref, purchase_ids)
            if purchases:
                purchase_ids.append(purchases[0].id)
            self.save_errors(errors, warnings)
        self.purchase_ids = [(6, 0, list(set(purchase_ids)))]

    def action_find(self):
        self.line_ids.unlink()
        self.find_purchases()
        self.step = 1
        return self._reopen_view()

    def action_back(self):
        self.step = 0
        return self._reopen_view()

    def action_invoice(self):
        wizard = self.env['purchase.order.invoice'].with_context({
            'active_ids': self.purchase_ids.ids,
            'active_model': 'purchase.order',
        }).create({
            'method': self.method,
            'join_purchases': self.join_purchases,
        })
        action = wizard.action_invoice()
        if action is True:
            return wizard.action_view_invoice()
        return action


class PurchaseOrderInvoiceRefsLines(models.TransientModel):
    _name = 'purchase.order.invoice_ref.lines'
    _description = 'Purchase order invoice by refs lines'
    _order = 'ref'

    wizard_id = fields.Many2one(
        comodel_name='purchase.order.invoice_refs',
        string='Wizard',
    )
    type = fields.Selection(
        selection=[
            ('error', 'Error'),
            ('warning', 'Warning'),
        ],
        string='Type',
        default='error',
    )
    name = fields.Char(
        string='Error message',
        required=True,
    )
    ref = fields.Char(
        string='Reference',
        required=True,
    )
