###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging
from datetime import datetime

import odoo.addons.decimal_precision as dp
from odoo import _, api, exceptions, fields, models
from odoo.tools import float_compare

_log = logging.getLogger(__name__)


class SimulatorSale(models.TransientModel):
    _name = 'simulator.sale'
    _description = 'Simulator Sale'

    state = fields.Selection(
        string='State',
        selection=[
            ('step_1', 'Step 1'),
            ('step_2', 'Step 2'),
            ('step_done', 'Done'),
        ],
        required=True,
        default='step_1',
    )
    order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        required=True,
        default=lambda self: self.env.context.get('active_id', None),
    )
    lines = fields.One2many(
        comodel_name='simulator.sale.line',
        inverse_name='sale_id',
        string='Lines',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.user.company_id,
    )
    shipping = fields.Selection(
        string='Shipping',
        selection=[
            ('10', 'UPS Standard'),
            ('11', 'UPS Express 9:00 a.m'),
            ('12', 'UPS Express 10:30 a.m'),
            ('13', 'UPS Express by 12:00 a.m'),
            ('20', 'Express delivery by forwarding agency'),
            ('30', 'Standard Shipping'),
        ],
        default='13',
    )

    @api.multi
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

    @api.multi
    def action_to_step_2(self):
        self.ensure_one()
        order_lines = self.order_id.mapped(
            'order_line').filtered(lambda l: l.is_simulator is True)
        ede = self.company_id.ede_client()
        client = ede.wsd_connection()
        items = []
        for sequence, line in enumerate(order_lines):
            items.append({
                'ID': sequence,
                'ProductID': line.product_id.barcode,
                'Quantity': line.product_uom_qty,
                'Date': self.order_id.date_order,
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
        simulation_danger = False
        simulation_protocol = False
        if plines:
            simulation_protocol = True
        for sequence, line in enumerate(order_lines):
            data = {
                'sale_id': self.id,
                'sale_line_id': line.id,
                'sequence': sequence
            }
            for sline in slines:
                if int(sline.find('ID').text) == sequence:
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
                if int(pline.find('ID').text) == sequence:
                    msg = pline.find('Text').text
                    if not line.product_id.barcode:
                        msg += _(' .Not EAN13 code.')
                    data['ede_msg'] = msg
                    data['is_ede_danger'] = True
            self.env['simulator.sale.line'].create(data)
        danger_lines = self.mapped('lines').filtered(
            lambda l: l.is_ede_danger is True)
        if danger_lines:
            simulation_danger = True
        if not simulation_danger and not simulation_protocol:
            self.state = 'step_2'
            return self._reopen_view()
        msg = _('<h3>Error Simulation Sale Order</h3><p>')
        if simulation_danger:
            msg += _('<li>Danger Material</li></p>')
            self.order_id.message_post(body=msg)
        if simulation_protocol:
            msg += _('<li>Protocol Errors</li></p>')
            self.order_id.message_post(body=msg)
        self.state = 'step_2'
        self.order_id.ede_workflow_state = 'simulated'
        return self._reopen_view()

    @api.multi
    def action_to_step_done(self):
        if not self.lines:
            raise exceptions.Warning(_('EDE not Return Simulation Products'))
        for line in self.lines:
            data = {}
            if line.is_ede_danger:
                data['is_ede_danger'] = True
            else:
                data['is_ede_danger'] = False
            if line.is_cost_changed:
                list_price = line.product_list_price
                if line.supplierinfo:
                    line.sudo().supplierinfo.price = line.ede_cost_price
                else:
                    self.env['product.supplierinfo'].sudo().create({
                        'product_tmpl_id': line.product_id.product_tmpl_id.id,
                        'name': self.order_id.company_id.ede_supplier_id.id,
                        'price': line.ede_cost_price,
                    })
                line.sudo().product_id.product_tmpl_id.lst_price = list_price
                if line.discount:
                    line.margin = (1 - line.ede_cost_price / (
                        line.price_unit * (1 - (line.discount / 100)))) * 100
                else:
                    line.margin = (1 - (
                        line.ede_cost_price / line.price_unit)) * 100
                line.sale_line_id.write(data)
                line.sudo().product_id.lst_price = list_price
        self.order_id.write({'ede_workflow_state': 'simulated'})
        self.state = 'step_done'
        return {'type': 'ir.actions.act_window_close'}


class SimulatorSaleLine(models.TransientModel):
    _name = 'simulator.sale.line'
    _description = 'Simulator Sale Line'

    sale_id = fields.Many2one(
        comodel_name='simulator.sale',
        string='sale_id',
        required=True,
        ondelete='cascade',
    )
    sale_line_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Sale Line',
        required=True,
        ondelete='cascade',
    )
    cost_price = fields.Float(
        related='sale_line_id.product_id.standard_price',
        string='Odoo Cost',
        digits=dp.get_precision('Product Price'),
    )
    product_uom_qty = fields.Float(
        related='sale_line_id.product_uom_qty',
    )
    product_uom = fields.Many2one(
        related='sale_line_id.product_uom',
    )
    product_id = fields.Many2one(
        related='sale_line_id.product_id',
    )
    product_list_price = fields.Float(
        related='sale_line_id.product_id.list_price',
    )
    discount = fields.Float(
        related='sale_line_id.discount',
    )
    price_unit = fields.Float(
        related='sale_line_id.price_unit',
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
        string='EDE Unit',
    )
    ede_quantity_available = fields.Integer(
        string='EDE Qty',
    )
    is_cost_changed = fields.Boolean(
        string='Cost Changed',
        compute='_compute_is_cost_changed',
        store=True,
    )
    ede_msg = fields.Char(
        string='EDE Msg',
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
        compute='_compute_line_color',
    )

    @api.one
    @api.depends('ede_cost_price')
    def _compute_is_cost_changed(self):
        self.is_cost_changed = bool(
            float_compare(self.cost_price, self.ede_cost_price, 2) != 0)

    @api.one
    @api.depends('sale_line_id')
    def _compute_supplierinfo(self):
        supplier = self.sale_id.company_id.ede_supplier_id
        supplier_infos = self.sale_line_id.product_id.product_tmpl_id.mapped(
            'seller_ids').filtered(lambda l: l.name.id == supplier.id)
        self.supplierinfo = supplier_infos and supplier_infos[0] or None

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
            next_week = float('%s.%s' % (year, week + 1))
            future = [s for s in schedules.keys() if s > this_week]
            friday = [s for s in schedules.keys() if s == next_week]
            week_day = datetime.today().isoweekday()
            if not future:
                self.line_color = 'green'
            elif len(future) == len(schedules) and week_day != 5:
                self.line_color = 'red'
            elif friday and week_day == 5:
                self.line_color = 'green'
            else:
                self.line_color = 'orange'
        except Exception:
            self.line_color = 'grey'
            return
