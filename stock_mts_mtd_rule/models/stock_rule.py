###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare, float_is_zero


class StockRule(models.Model):
    _inherit = 'stock.rule'

    action = fields.Selection(
        selection_add=[
            ('split_procurement_mts_mtd', 'Choose between MTS and MTD'),
        ],
    )
    mts_rule_id = fields.Many2one(
        comodel_name='stock.rule',
        string='MTS Rule',
    )
    mtd_rule_id = fields.Many2one(
        comodel_name='stock.rule',
        string='MTD Rule',
    )

    @api.constrains('action', 'mts_rule_id', 'mtd_rule_id')
    def _check_mts_mtd_rule(self):
        for rule in self:
            if rule.action == 'split_procurement_mts_mtd':
                if not rule.mts_rule_id or not rule.mtd_rule_id:
                    msg = _('No MTS or MTD rule configured on procurement '
                            'rule: %s!') % rule.name
                    raise ValidationError(msg)

    def _get_qty_available_for_mtd_qty(
            self, product, product_location, product_uom):
        return product.uom_id._compute_quantity(
            product_location.virtual_available, product_uom)

    @api.multi
    def get_mtd_qty_to_order(self, product, product_qty, product_uom, values):
        self.ensure_one()
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        src_location_id = self.mts_rule_id.location_src_id.id
        product_location = product.with_context(location=src_location_id)
        qty_available = self._get_qty_available_for_mtd_qty(
            product, product_location, product_uom)
        if float_compare(qty_available, 0.0, precision_digits=precision) > 0:
            if float_compare(qty_available, product_qty,
                             precision_digits=precision) >= 0:
                return 0.0
            else:
                return product_qty - qty_available
        return product_qty

    def _run_split_procurement_mts_mtd(
            self, product_id, product_qty, product_uom, location_id, name,
            origin, values):
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        needed_qty = self.get_mtd_qty_to_order(
            product_id, product_qty, product_uom, values)
        if float_is_zero(needed_qty, precision_digits=precision):
            getattr(self.mts_rule_id, '_run_%s' % self.mts_rule_id.action)(
                product_id, product_qty, product_uom, location_id, name,
                origin, values)
        elif float_compare(
                needed_qty, product_qty, precision_digits=precision) == 0.0:
            getattr(self.mtd_rule_id, '_run_%s' % self.mtd_rule_id.action)(
                product_id, product_qty, product_uom, location_id, name,
                origin, values)
        else:
            mts_qty = product_qty - needed_qty
            getattr(self.mts_rule_id, '_run_%s' % self.mts_rule_id.action)(
                product_id, mts_qty, product_uom, location_id, name, origin,
                values)
            getattr(self.mtd_rule_id, '_run_%s' % self.mtd_rule_id.action)(
                product_id, needed_qty, product_uom, location_id, name,
                origin, values)
        return True
