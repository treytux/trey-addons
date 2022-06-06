###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models


class PurchaseOrderInvoiceRefs(models.TransientModel):
    _name = 'purchase.order.invoice_refs'
    _description = 'Purchase order invoice by refs'

    @api.model
    def _default_method(self):
        model = self.env['purchase.order.invoice']
        return model._fields['method'].default(model)

    @api.model
    def _get_method_selection(self):
        return self.env['purchase.order.invoice']._fields['method'].selection

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
        selection=_get_method_selection,
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
        string='step',
    )

    def _reopen_view(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.ids[0],
            'res_model': self._name,
            'target': 'new',
            'context': {}}

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

    def find_purchases(self):
        self.ensure_one()
        purchase_ids = []
        for ref in self.references_to_list():
            purchase = self.purchase_ids.search([
                ('partner_id', '=', self.partner_id.id),
                '|',
                ('name', '=', ref),
                ('partner_ref', '=', ref)])
            if len(purchase) > 1:
                self._error(_('Return more than one order'), ref)
                continue
            if len(purchase) == 0:
                self._error(_('Not found'), ref)
                continue
            if purchase.state not in ['purchase', 'done']:
                self._error(
                    _('Purchase in state %s, must be confirmed or done') % (
                        purchase.state), ref)
                continue
            if purchase.id in purchase_ids:
                self._warning(_('Reference duplicate, ignore one'), ref)
                continue
            if purchase.invoice_ids:
                self._warning(_('Purchase already invoiced'), ref)
                continue
            purchase_ids.append(purchase.id)
        self.purchase_ids = [(6, 0, purchase_ids)]

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
            'active_model': 'purchase.order'
        }).create({
            'method': self.method,
            'join_purchases': self.join_purchases,
        })
        return wizard.action_view_invoice()


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
