###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, fields, models


class MrpProductionFinishedDetail(models.TransientModel):
    _name = 'mrp.production.finished_detail'
    _description = 'Finished products production order move lines wizard'

    production_id = fields.Many2one(
        comodel_name='mrp.production',
        string='Production Order',
        required=True,
        readonly=True,
    )
    is_locked = fields.Boolean(
        related='production_id.is_locked',
        string='Is Locked',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
        readonly=True,
    )
    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Unit of Measure',
        required=True,
        readonly=True,
    )
    qty_total = fields.Float(
        string='Quantity total',
        readonly=True,
    )
    qty_done = fields.Float(
        compute='_compute_qty_done',
        string='Quantity done',
        readonly=True,
    )
    line_ids = fields.One2many(
        comodel_name='mrp.production.finished_detail.line',
        inverse_name='wizard_id',
        string='Details',
    )

    @api.depends('line_ids')
    def _compute_qty_done(self):
        for detail in self:
            detail.qty_done = sum(detail.line_ids.mapped('qty_done'))

    @api.model
    def create_wizard(self, production_id, product_id):
        mo = self.env['mrp.production'].browse(production_id)
        move_lines = mo.finished_move_line_ids.filtered(
            lambda m: m.product_id.id == product_id)
        wizard = self.create({
            'production_id': production_id,
            'product_id': product_id,
            'product_uom_id': move_lines[0].product_uom_id.id,
            'qty_total': move_lines[0].move_id.product_uom_qty,
        })
        for move_line in move_lines:
            wizard.line_ids.create({
                'wizard_id': wizard.id,
                'result_package_id': move_line.result_package_id.id,
                'lot_id': move_line.lot_id.id,
                'qty_done': move_line.qty_done,
            })
        if wizard.qty_done != wizard.qty_total:
            wizard.line_ids.create({
                'wizard_id': wizard.id,
                'qty_done': wizard.qty_total - wizard.qty_done,
            })
        return wizard

    def action_confirm(self):
        self.ensure_one()
        if self.qty_done > self.qty_total:
            raise exceptions.ValidationError(
                _('The total quantity is %s, but you complete %s.') % (
                    self.qty_total, self.qty_done))
        move = self.production_id.move_finished_ids.filtered(
            lambda m: m.product_id == self.product_id)
        move.move_line_ids.unlink()
        diff = self.qty_total - sum(self.line_ids.mapped('qty_done'))
        if diff:
            self.line_ids.create({
                'wizard_id': self.id,
                'qty_done': diff,
            })
        group_lines = {}
        for line in self.line_ids:
            key = ','.join([
                str(line.result_package_id.id or 0), str(line.lot_id.id or 0)])
            group_lines.setdefault(key, 0)
            group_lines[key] += line.qty_done
        for key, qty_done in group_lines.items():
            package_id, lot_id = key.split(',')
            move.move_line_ids.create({
                'move_id': move.id,
                'product_id': move.product_id.id,
                'location_id': move.location_id.id,
                'production_id': move.raw_material_production_id.id,
                'location_dest_id': move.location_dest_id.id,
                'product_uom_id': move.product_uom.id,
                'product_uom_qty': qty_done,
                'qty_done': qty_done,
                'lot_produced_id': int(lot_id) or None ,
                'result_package_id': int(package_id) or False,
            })


class MrpProductionFinishedDetailLine(models.TransientModel):
    _name = 'mrp.production.finished_detail.line'
    _description = 'Finished products production order move lines wizard, line'

    wizard_id = fields.Many2one(
        comodel_name='mrp.production.finished_detail',
        string='Wizard',
    )
    product_id = fields.Many2one(
        related='wizard_id.product_id',
        string='Product',
    )
    result_package_id = fields.Many2one(
        comodel_name='stock.quant.package',
        string='Packaging',
    )
    lot_id = fields.Many2one(
        comodel_name='stock.production.lot',
        string='Lot/Serial',
        domain='[("product_id", "=", product_id)]',
    )
    qty_done = fields.Integer(
        string='Quantity',
        default=0,
    )
