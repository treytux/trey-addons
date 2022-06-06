###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, exceptions, fields, models


class StockPackageDummyRead(models.TransientModel):
    _inherit = 'stock.package_dummy.read'

    production_id = fields.Many2one(
        comodel_name='mrp.production',
        string='Production',
    )

    def _simulate_from_mrp_production(self, dummies):
        mo = self.production_id
        if not mo:
            self.log(_('No production order assigned'))
        total = {}
        for barcode, dummy in dummies.items():
            if not dummy.product_id and len(mo.finished_move_line_ids) > 1:
                msg = _(
                    'This dummy label need a product assigned. This happens '
                    'because the production has made more than one product'
                )
                self.log(msg, barcode)
                continue
            product = dummy.product_id or mo.finished_move_line_ids.product_id
            moves = mo.finished_move_line_ids.filtered(
                lambda m: m.product_id == product)
            if not moves:
                msg = (
                    _('Not exists stock moves for product "%s"')
                    % product.name
                )
                self.log(msg , barcode)
                continue
            packages = mo.finished_move_line_ids.mapped(
                'result_package_id.name')
            if barcode in packages:
                self.log(
                    _('Barcode already in use for this production, duplicate '
                      'read'),
                    barcode)
                continue
            qty = dummy.packaging_id and dummy.packaging_id.qty or 1
            if product.id not in total:
                moves = moves.filtered(lambda m: not m.result_package_id)
                total[product.id] = sum(moves.mapped('qty_done'))
            total[product.id] -= qty
            if total[product.id] < 0:
                msg = (
                    _('Not enough quantity for the product "%s"')
                    % product.name
                )
                self.log(msg, barcode)
                continue

    def _run_create_packages_from_mrp_production(self):
        self.ensure_one()
        barcodes = self.barcodes_to_list()
        dummy_obj = self.env['stock.quant.package_dummy']
        mo = self.production_id
        for barcode in barcodes:
            dummy = dummy_obj.search_from_barcode(barcode)
            if not dummy:
                continue
            if not dummy.product_id and len(mo.finished_move_line_ids) > 1:
                raise exceptions.UserError(_(
                    'This dummy label need a product assigned. This happens '
                    'because the production has made more than one product'))
            product = dummy.product_id or mo.finished_move_line_ids.product_id
            moves = mo.finished_move_line_ids.filtered(
                lambda m: m.product_id == product)
            if not moves:
                raise exceptions.UserError(
                    _('Not exists stock moves for product "%s"') % (
                        product.name))
            qty = dummy.packaging_id and dummy.packaging_id.qty or 1
            moves = moves.filtered(lambda m: not m.result_package_id)
            if sum(moves.mapped('qty_done')) < qty:
                raise exceptions.UserError(
                    _('Not enough occurred to create package %s') % (
                        barcode))
            pack = dummy.create_pack(barcode)
            data = {
                'result_package_id': pack.id,
                'qty_done': qty,
                'lot_id': dummy.lot_id.id,
            }
            if moves[0].qty_done == qty:
                moves[0].write(data)
            else:
                moves[0].copy(data)
                moves[0].qty_done -= qty
