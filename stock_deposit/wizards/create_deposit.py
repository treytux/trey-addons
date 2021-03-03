###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CreateDeposit(models.TransientModel):
    _name = 'create.deposit'
    _description = 'Create a deposit location'

    name = fields.Char(
        string='Deposit name',
        required=True,
    )
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        required=True,
    )

    @api.constrains('name')
    def _check_name_unique(self):
        deposits = self.env['stock.location'].search([
            ('id', '!=', self.id),
            ('name', '=', self.name),
        ])
        if deposits:
            raise UserError(_('Deposit name must be unique!'))

    @api.constrains('warehouse_id')
    def _check_deposit_parent_id(self):
        if not self.warehouse_id.deposit_parent_id:
            raise UserError(_(
                '\'Deposit parent\' field in \'%s\' warehouse can not be '
                'empty. You must fill it from the Warehouse/Configuration/'
                'Warehouse Management/Warehouses menuitem.') % (
                self.warehouse_id.name))

    @api.multi
    def action_create_deposit(self):
        deposit_loc = self.env['stock.location'].create({
            'name': self.name,
            'location_id': self.warehouse_id.deposit_parent_id.id,
            'usage': 'internal',
        })
        self.warehouse_id.int_type_id.active = True
        wh2deposit_route = self.env['stock.location.route'].create({
            'name': _(
                '%s -> %s' % (self.warehouse_id.name, deposit_loc.name)),
            'warehouse_selectable': True,
            'product_selectable': False,
        })
        data_rule = {
            'name': _(
                '%s -> %s' % (
                    self.warehouse_id.lot_stock_id.name, deposit_loc.name)),
            'action': 'pull',
            'picking_type_id': self.warehouse_id.int_type_id.id,
            'location_src_id': self.warehouse_id.lot_stock_id.id,
            'location_id': deposit_loc.id,
            'procure_method': 'make_to_stock',
            'group_propagation_option': 'propagate',
            'propagate': True,
        }
        data_wh2deposit_rule = data_rule.copy()
        data_wh2deposit_rule.update({
            'route_id': wh2deposit_route.id,
            'sequence': 20,
        })
        self.env['stock.rule'].create(data_wh2deposit_rule)
        buy_route = self.env.ref('purchase_stock.route_warehouse0_buy')
        data_buy_rule = data_rule.copy()
        data_buy_rule.update({
            'route_id': buy_route.id,
            'sequence': 10,
        })
        self.env['stock.rule'].create(data_buy_rule)
        view = self.env.ref('stock_deposit.create_deposit_done_wizard')
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view.id, 'form')],
            'target': 'new',
        }
