###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, exceptions, models


class PickingManifestReport(models.TransientModel):
    _name = 'picking.manifest.report'
    _description = 'Picking Manifest Report'

    def _validate_pickings(self):
        active_ids = self._context.get('active_ids')
        pickings = self.env['stock.picking'].browse(active_ids)
        no_carrier = pickings.filtered(lambda p: not p.carrier_id)
        if len(no_carrier) >= 1:
            raise exceptions.UserError(_('''
                Picking(s) %s do(es) not have carrier, set one and try again.
            ''') % ", ".join(no_carrier.mapped('name')))
        has_manifest = pickings.filtered(lambda p: p.manifest_id)
        if len(has_manifest) >= 1:
            raise exceptions.UserError(_('''
                Picking(s) %s already exist(s) in previous manifest(s),
                filter out by "Not in manifest" and try again.
            ''') % ", ".join(has_manifest.mapped('name')))
        return {'type': 'ir.actions.act_window_close'}

    def _get_manifests(self):
        active_ids = self._context.get('active_ids')
        pickings = self.env['stock.picking'].browse(active_ids)
        manifests = self.env['delivery.carrier.manifest']
        for picking in pickings:
            if picking.carrier_id not in manifests.mapped('carrier_id'):
                manifests |= manifests.create({
                    'carrier_id': picking.carrier_id.id,
                    'picking_ids': [(6, 0, [picking.id])],
                })
            else:
                manifests.filtered(
                    lambda m: m.carrier_id == picking.carrier_id).write({
                        'picking_ids': [(4, picking.id)],
                    })
        return manifests

    def button_print(self):
        self._validate_pickings()
        docs = self._get_manifests()
        return self.env.ref(
            'delivery_carrier_manifest.report_carrier_manifest_create'
        ).report_action(docs)
