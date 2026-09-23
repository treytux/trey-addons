# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from datetime import datetime
from openerp import fields, api, models, exceptions, _
import openerp.addons.decimal_precision as dp
from openerp.tools import float_compare


class SimulatorPurchase(models.TransientModel):
    _name = 'simulator.purchase'
    _description = 'Simulator Purchase'

    state = fields.Selection(
        string='State',
        selection=[('step_1', 'Step 1'),
                   ('step_2', 'Step 2'),
                   ('step_done', 'Done')],
        required=True,
        default='step_1')
    lines = fields.One2many(
        comodel_name='simulator.purchase.line',
        inverse_name='purchase_id',
        string='Lines')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.user.company_id)
    shipping = fields.Selection(
        string='Shipping',
        selection=[('10', 'UPS Standard'),
                   ('11', 'UPS Express 9:00 a.m'),
                   ('12', 'UPS Express 10:30 a.m'),
                   ('13', 'UPS Express by 12:00 a.m'),
                   ('20', 'Express delivery by forwarding agency'),
                   ('30', 'Standard Shipping')],
        default='13')

    @api.multi
    def _reopen_view(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.ids[0],
            'res_model': self._name,
            'target': 'new',
            'context': {}}

    @api.multi
    def action_to_step_2(self):
        self.ensure_one()
        purchase_order = self.env['purchase.order'].browse(
            self.env.context['active_id'])
        order_lines = purchase_order.mapped('order_line')
        ede = self.company_id.ede_client()
        client = ede.connection()
        items = []
        for line in order_lines:
            items.append({
                'ID': line.id,
                'ProductID': line.product_id.ean13,
                'Quantity': line.product_qty,
                'Date': purchase_order.date_order,
            })
        payload = {
            'ShipmentTypeCode': self.shipping,
            'Items': {'Item': items},
        }
        credentials = self.company_id.ede_credentials()
        simulation = ede.simulate_order(
            client=client, credentials=credentials, payload=payload)
        if simulation is None:
            raise exceptions.Warning(_('EDE not Return Simulation Products'))
        else:
            slines = simulation.findall(
                ".//SalesOrderSimulateConfirmation/Items/Item")
            plines = simulation.findall(
                ".//SalesOrderSimulateConfirmation/Protocol/Item")
        if simulation is None:
            raise exceptions.Warning(_('EDE not Return Simulation Products'))
        simulation_danger = False
        simulation_protocol = False
        if plines:
            simulation_protocol = True
        for line in order_lines:
            data = {
                'purchase_id': self.id,
                'purchase_line_id': line.id,
            }
            for sline in slines:
                if int(sline.find('ID').text) == line.id:
                    if sline.find('DangerMaterial').text == 'X':
                        data['is_ede_danger'] = True
                    else:
                        data['is_ede_danger'] = False
                    data['ede_cost_price'] = float(sline.find(
                        'Price').text)
                    data['ede_position_price'] = float(sline.find(
                        'PositionPrice').text) or 0.00
                    data['ede_quantity_unit'] = sline.find(
                        'QuantityUnit').text or ''
                    data['ede_quantity_available'] = int(sline.find(
                        'QuantityAvailable').text) or 0
                    data['ede_msg'] = sline.find(
                        'Schedules').text or _('No Messages')
            for pline in plines:
                if int(pline.find('ID').text) == line.id:
                    data['ede_msg'] = pline.find('Text').text
                    data['is_ede_danger'] = True
            self.env['simulator.purchase.line'].create(data)
        danger_lines = self.mapped('lines').filtered(
            lambda l: l.is_ede_danger is True)
        if danger_lines:
            simulation_danger = True
        if not simulation_danger and not simulation_protocol:
            self.state = 'step_2'
            return self._reopen_view()
        msg = _('<h3>Warning Simulation Purchase Order</h3><p>')
        if simulation_danger:
            msg += _('<li> Danger Material</li></p>')
            purchase_order.message_post(body=msg)
        if simulation_protocol:
            msg += _('<li> Protocol Errors</li></p>')
            purchase_order.message_post(body=msg)
        self.state = 'step_2'
        purchase_order.adarra_ede_state = 'simulated'
        return self._reopen_view()

    @api.multi
    def action_to_step_done(self):
        if not self.lines:
            raise exceptions.Warning(_('EDE not Return Simulation Products'))
        purchase_order = self.lines[0].purchase_line_id.order_id
        for line in self.lines:
            data = {}
            if line.is_ede_danger:
                data['is_ede_danger'] = True
            else:
                data['is_ede_danger'] = False
            if line.is_cost_changed:
                product = line.purchase_line_id.product_id
                margin = (1 - (
                    line.ede_cost_price / product.lst_price)) * 100
                product.write({
                    'supplier_price': line.ede_cost_price,
                    'margin': margin,
                })
                product.update_standard_price()
                data['price_unit'] = line.ede_cost_price
            line.purchase_line_id.write(data)
        purchase_order.button_dummy()
        purchase_order.write({
            'adarra_ede_state': 'simulated',
            })
        self.state = 'step_done'
        return {'type': 'ir.actions.act_window_close'}


class SimulatorPurchaseLine(models.TransientModel):
    _name = 'simulator.purchase.line'
    _description = 'Simulator Purchase Line'

    purchase_id = fields.Many2one(
        comodel_name='simulator.purchase',
        string='purchase_id',
        required=True,
        ondelete='cascade',
    )
    purchase_line_id = fields.Many2one(
        comodel_name='purchase.order.line',
        string='Purchase Line',
    )
    cost_price = fields.Float(
        related='purchase_line_id.price_unit',
        string='Odoo Cost',
        digits=dp.get_precision('Product Price'),
    )
    product_qty = fields.Float(
        related='purchase_line_id.product_qty',
    )
    product_uom = fields.Many2one(
        related='purchase_line_id.product_uom',
    )
    product_id = fields.Many2one(
        related='purchase_line_id.product_id',
    )
    discount = fields.Float(
        related='purchase_line_id.discount',
    )
    price_unit = fields.Float(
        related='purchase_line_id.price_unit',
    )
    ede_cost_price = fields.Float(
        string='EDE Cost',
        digits=dp.get_precision('Product Price'),
    )
    ede_position_price = fields.Float(
        string='EDE Total',
        digits=dp.get_precision('Total Price'),
    )
    ede_quantity_unit = fields.Char(
        string='EDE Unit')
    ede_quantity_available = fields.Integer(
        string='EDE Qty',
    )
    is_cost_changed = fields.Boolean(
        string='Cost Changed',
        compute='_compute_is_cost_changed',
        store=True,
    )
    ede_msg = fields.Char(
        string='EDE Msg'
    )
    is_ede_danger = fields.Boolean(
        string='EDE Danger',
    )
    supplierinfo = fields.Many2one(
        comodel_name='product.supplierinfo',
        compute='_compute_supplierinfo',
        store=True,
    )
    line_color = fields.Selection(
        string='Color',
        selection=[
            ('red', 'Red'),
            ('orange', 'Orange'),
            ('green', 'Green'),
            ('grey', 'Grey'),
        ],
        compute='_compute_line_color')

    @api.one
    @api.depends('cost_price', 'ede_cost_price')
    def _compute_is_cost_changed(self):
        self.is_cost_changed = bool(
            float_compare(self.cost_price, self.ede_cost_price, 2) != 0)

    @api.one
    @api.depends('purchase_line_id')
    def _compute_supplierinfo(self):
        supplier = self.purchase_id.company_id.ede_supplier_id
        supplier_infos = \
            self.purchase_line_id.product_id.product_tmpl_id.mapped(
                'seller_ids').filtered(lambda l: l.name.id == supplier.id)
        return supplier_infos and supplier_infos[0] or None

    @api.one
    @api.depends('ede_msg')
    def _compute_line_color(self):
        try:
            def parser_schedules(txt):
                txt = txt.replace('Geplante Liefertermine:', '')
                txt = [t for t in txt.split(';') if t]
                txt = [[s.strip() for s in t.split('ST in KW')] for t in txt]
                res = {}
                for qty, week in txt:
                    week = week.split('.')
                    week = float('%s.%s' % (week[1], week[0]))
                    res[week] = res.setdefault(week, 0) + float(qty)
                return res
            schedules = parser_schedules(self.ede_msg)
            year, week, dow = datetime.today().isocalendar()
            this_week = float('%s.%s' % (year, week))
            future = [s for s in schedules.keys() if s > this_week]
            if not future:
                self.line_color = 'green'
            elif len(future) == len(schedules):
                self.line_color = 'red'
            else:
                self.line_color = 'orange'
        except Exception:
            self.line_color = 'grey'
            return
