###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class PurchaseOrderInvoiceRefs(models.TransientModel):
    _inherit = 'purchase.order.invoice_refs'

    def add_errors(self, errors, warnings):
        for error in errors:
            self._error(error[0], error[1])
        for warning in warnings:
            self._warning(warning[0], warning[1])

    def check_picking_errors(self, pickings, purchases, purchase_ids, ref):
        errors = []
        warnings = []
        if len(pickings) > 1:
            errors.append((_('Return more than one picking.'), ref))
            return errors, warnings
        if len(pickings) == 0:
            errors.append((_('Picking not found.'), ref))
            return errors, warnings
        if len(purchases) > 1:
            errors.append((_(
                'Picking return more than one purchase.'), ref))
            return errors, warnings
        if len(purchases) == 0:
            errors.append((_('Picking\'s purchase not found.'), ref))
            return errors, warnings
        if purchases.state not in ['purchase', 'done']:
            errors.append((_(
                'Picking\'s purchase in state %s, must be confirmed or done.'
            ) % (purchases.state), ref))
            return errors, warnings
        if purchases.id in purchase_ids:
            warnings.append((_(
                'Picking\'s purchase reference duplicate, ignore one.'), ref))
            return errors, warnings
        if purchases.invoice_ids:
            warnings.append((_('Picking\'s purchase already invoiced.'), ref))
            return errors, warnings

    def search_by_reference(self, ref, purchase_ids):
        errors = []
        warnings = []
        picking_obj = self.env['stock.picking']
        purchase_obj = self.env['purchase.order']
        purchases, errors, warnings = super().search_by_reference(
            ref, purchase_ids)
        if purchases:
            return purchases, errors, warnings
        pickings = picking_obj.search([
            ('partner_id', '=', self.partner_id.id),
            ('picking_type_code', '=', 'incoming'),
            ('picking_supplier_ref', '=', ref),
        ])
        is_picking_found = len(pickings) == 1 and pickings.state == 'done'
        if is_picking_found:
            purchases = purchase_obj.search([
                ('picking_ids', 'in', pickings.ids),
            ])
            if self.is_purchase_found(purchases, purchase_ids):
                errors = []
                warnings = []
                return purchases, errors, warnings
        picking_errors, picking_warnings = self.check_picking_errors(
            pickings, purchases, purchase_ids, ref)
        for picking_error in picking_errors:
            errors.append(picking_error)
        for picking_warning in picking_warnings:
            warnings.append(picking_warning)
        return purchases, errors, warnings
