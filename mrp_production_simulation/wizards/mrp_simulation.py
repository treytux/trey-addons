# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, _, exceptions


class WizMrpSimulation(models.TransientModel):
    _name = 'wiz.mrp.simulation'
    _description = 'Simulation for a mrp'

    name = fields.Char(
        string='Empty')
    main_product_id = fields.Many2one(
        comodel_name='product.product',
        string='Main product',
        readonly=True)
    main_qty2produce = fields.Integer(
        string='Quantity to produce',
        readonly=True)
    real_qty2produce = fields.Integer(
        string='Real quantity to produce',
        readonly=True)
    virtual_qty2produce = fields.Integer(
        string='Virtual quantity to produce',
        readonly=True)
    line_ids = fields.One2many(
        comodel_name='wiz.mrp.simulation.line',
        inverse_name='simulation_id',
        string='Simulation lines',
        readonly=True)
    lines_to_buy_ids = fields.One2many(
        comodel_name='wiz.mrp.simulation.buy.line',
        inverse_name='buy_simulation_id',
        string='Buy simulation lines',
        readonly=True)
    lines_to_produce_ids = fields.One2many(
        comodel_name='wiz.mrp.simulation.manufacture.line',
        inverse_name='manufacture_simulation_id',
        string='Manufacture simulation lines',
        readonly=True)

    def get_qty_pending(self, manuf_route, buy_route, product, product_qty):
        qty_pending_buy = 0
        qty_pending_produce = 0
        qty_pending = product.qty_available - product_qty
        if product.type == 'service':
            return 0, 0
        if manuf_route in product.route_ids:
            if qty_pending < 0:
                qty_pending_produce = - qty_pending
        elif buy_route in product.route_ids:
            if qty_pending < 0:
                qty_pending_buy = - qty_pending
        return qty_pending_produce, qty_pending_buy

    def get_product_route(self, manuf_route, buy_route, product):
        product_route = ''
        if manuf_route in product.route_ids:
            product_route = 'manufacture'
        elif buy_route in product.route_ids:
            product_route = 'buy'
        return product_route

    def get_bom_child_ids(self, obj, bom_line, level, res=None):
        if not bom_line.child_line_ids.exists():
            return True
        manuf_route = self.env.ref('mrp.route_warehouse0_manufacture')
        buy_route = self.env.ref('purchase.route_warehouse0_buy')
        assert manuf_route.exists(), 'Manufacture route should exist!'
        assert buy_route.exists(), 'Buy route should exist!'
        for child_bom_line in bom_line.child_line_ids:
            product_parent_id = \
                child_bom_line.bom_id.product_id and \
                child_bom_line.bom_id.product_id.id or\
                child_bom_line.bom_id.product_tmpl_id.\
                product_variant_ids[0].id
            qty_pending_produce, qty_pending_buy = (
                self.get_qty_pending(
                    manuf_route, buy_route,
                    child_bom_line.product_id,
                    child_bom_line.product_qty *
                    obj.product_qty * bom_line.product_qty))
            qty_available = (
                child_bom_line.product_id.type == 'service' and 999.99 or
                child_bom_line.product_id.qty_available)
            virtual_available = (
                child_bom_line.product_id.type == 'service' and 999.99 or
                child_bom_line.product_id.virtual_available)
            res.append({
                'product_id': child_bom_line.product_id.id,
                'quantity': (
                    child_bom_line.product_qty *
                    obj.product_qty * bom_line.product_qty),
                'product_parent_id': product_parent_id,
                'qty_available': qty_available,
                'virtual_available': virtual_available,
                'qty_pending_buy': qty_pending_buy,
                'qty_pending_produce': qty_pending_produce,
                'product_route': self.get_product_route(
                    manuf_route, buy_route,
                    child_bom_line.product_id),
                'level': level})
            self.get_bom_child_ids(obj, child_bom_line, level + 1, res)
        return True

    def get_product_components(self, obj, product):
        '''
        Returns a dictionary with the information calculated for each of the
        products that are needed to obtain the manufactured product.
        '''
        res = []
        manuf_route = self.env.ref('mrp.route_warehouse0_manufacture')
        buy_route = self.env.ref('purchase.route_warehouse0_buy')
        assert manuf_route.exists(), 'Manufacture route should exist!'
        assert buy_route.exists(), 'Buy route should exist!'
        qty_pending_produce, qty_pending_buy = self.get_qty_pending(
            manuf_route, buy_route, product, obj.product_qty)
        if qty_pending_produce == 0:
            return res
        if obj._name == 'mrp.production':
            bom_id = obj.bom_id
        elif obj._name == 'mrp.bom':
            product = (
                obj.product_id or obj.product_tmpl_id.product_variant_ids[0])
            bom_id = product.bom_ids[0]
        else:
            raise exceptions.Warning(_(
                'Object %s not contemplated!' % obj._name))
        if not bom_id.exists():
            raise exceptions.Warning(_(
                'Mrp production %s has not defined any bill of materials. '
                'You must assign it!') % obj.name)
        if not product.bom_ids.exists():
            raise exceptions.Warning(_(
                'Product %s has not defined any bill of materials. '
                'You must assign it!') % product.name)
        bom = product.bom_ids[0]
        if len(product.bom_ids) > 1:
            bom = bom_id in product.bom_ids and bom_id or False
            if not bom:
                raise exceptions.Warning(_(
                    'The bill of material selected in the manufacturing order '
                    '%s does not belong to any of those defined for the '
                    'product to be manufactured %s.') % (
                        obj.name, product.name))
        for bom_line in bom.bom_line_ids:
            product_parent_id = (
                product in bom_line.bom_id.product_id and product.id or
                product in
                bom_line.bom_id.product_tmpl_id.product_variant_ids and
                product.id)
            if not product_parent_id:
                raise exceptions.Warning(_('Product parent is not found.'))
            level = 1
            qty_pending_produce, qty_pending_buy = self.get_qty_pending(
                manuf_route, buy_route, bom_line.product_id,
                bom_line.product_qty * obj.product_qty)
            product_route = self.get_product_route(
                manuf_route, buy_route, bom_line.product_id)
            qty_available = (
                bom_line.product_id.type == 'service' and 999.99 or
                bom_line.product_id.qty_available)
            virtual_available = (
                bom_line.product_id.type == 'service' and 999.99 or
                bom_line.product_id.virtual_available)
            res.append({
                'product_id': bom_line.product_id.id,
                'quantity': bom_line.product_qty * obj.product_qty,
                'product_parent_id': product_parent_id,
                'qty_available': qty_available,
                'virtual_available': virtual_available,
                'qty_pending_buy': qty_pending_buy,
                'qty_pending_produce': qty_pending_produce,
                'product_route': product_route,
                'level': level})
            if qty_pending_produce != 0:
                self.get_bom_child_ids(obj, bom_line, level + 1, res)
        return res

    def get_qty2produce(self, res, qty_type):
        '''
        Calculate the real quantity that can be produced consider the real or
        virtual stock defined in the variable 'qty_type'.
            min(qty_available / mrp_quantity) whose parent is the product to
                be manufactured.
            min(virtual_available / mrp_quantity) whose parent is the product
                to be manufactured.
        '''
        if not res['line_ids']:
            return res['main_qty2produce']
        return int(min([
            line[2][qty_type]
            for line in res['line_ids']
            if 'product_parent_id' in line[2] and
            line[2]['product_parent_id'] == res['main_product_id']]))

    def get_product2buy(self, simulation_lines):
        '''
        Calculate the total quantity that needs to be purchased to produce the
        main manufactured product.
        '''
        products2buy_group = {}
        products2buy = []
        for line in simulation_lines:
            if line['qty_pending_buy'] == 0:
                continue
            if line['product_id'] not in products2buy_group:
                products2buy_group[line['product_id']] = line[
                    'qty_pending_buy']
            else:
                products2buy_group[line['product_id']] += line[
                    'qty_pending_buy']
        for k, v in products2buy_group.iteritems():
            products2buy.append({
                'product_id': k,
                'qty_pending_buy': v})
        return products2buy

    def get_product2produce(self, simulation_lines):
        '''
        Calculate the total quantity that needs to be produced to produce the
        main manufactured product.
        '''
        products2produce_group = {}
        products2produce = []
        for line in simulation_lines:
            if line['qty_pending_produce'] == 0:
                continue
            if line['product_id'] not in products2produce_group:
                products2produce_group[line['product_id']] = line[
                    'qty_pending_produce']
            else:
                products2produce_group[line['product_id']] += line[
                    'qty_pending_produce']
        for k, v in products2produce_group.iteritems():
            products2produce.append({
                'product_id': k,
                'qty_pending_produce': v})
        return products2produce

    @api.multi
    def get_escandallo(self):
        view_id = self.env.ref('mrp_production_escandallo.escandallo_tree')
        product = self.main_product_id
        domain = [
            '|',
            ('bom_id.product_id', '=', product.id),
            ('bom_id.product_tmpl_id', '=', product.product_tmpl_id.id)]
        return {
            'type': 'ir.actions.act_window',
            'name': _('Escandallo'),
            'res_model': 'mrp.bom.line',
            'view_type': 'tree',
            'view_mode': 'tree',
            'view_id': view_id.id,
            'domain': domain,
            'target': 'new'}

    @api.model
    def default_get(self, fields):
        res = super(WizMrpSimulation, self).default_get(fields)
        active_model = self.env.context['active_model']
        active_id = self.env.context['active_id']
        obj = self.env[active_model].browse(active_id)
        if active_model == 'mrp.production':
            obj_product = obj.product_id
        elif active_model == 'mrp.bom':
            obj_product = (
                obj.product_id or obj.product_tmpl_id.product_variant_ids[0])
        lines = self.get_product_components(obj, obj_product)
        if 'line_ids' not in res:
            res['line_ids'] = []
        for line in lines:
            res['line_ids'].append((0, 0, line))
        res['main_product_id'] = obj_product.id
        res['main_qty2produce'] = obj.product_qty
        res['real_qty2produce'] = self.get_qty2produce(res, 'qty_available')
        res['virtual_qty2produce'] = self.get_qty2produce(
            res, 'virtual_available')
        lines2buy = self.get_product2buy(lines)
        if 'lines_to_buy_ids' not in res:
            res['lines_to_buy_ids'] = []
        for line in lines2buy:
            product = self.env['product.product'].browse(line['product_id'])
            if product.type == 'service':
                continue
            res['lines_to_buy_ids'].append((0, 0, line))
        lines2produce = self.get_product2produce(lines)
        if 'lines_to_produce_ids' not in res:
            res['lines_to_produce_ids'] = []
        for line in lines2produce:
            product = self.env['product.product'].browse(line['product_id'])
            if product.type == 'service':
                continue
            res['lines_to_produce_ids'].append((0, 0, line))
        return res

    @api.multi
    def button_accept(self):
        return {'type': 'ir.actions.act_window_close'}


class WizMrpSimulationLine(models.TransientModel):
    _name = 'wiz.mrp.simulation.line'
    _description = 'Simulation lines'

    name = fields.Char(
        string='Empty')
    simulation_id = fields.Many2one(
        comodel_name='wiz.mrp.simulation',
        string='Simulation')
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product')
    product_parent_id = fields.Many2one(
        comodel_name='product.product',
        string='Product parent')
    quantity = fields.Float(
        string='Need')
    qty_available = fields.Float(
        string='On hand')
    virtual_available = fields.Float(
        string='Forecast')
    qty_pending_buy = fields.Float(
        string='Pending buy')
    qty_pending_produce = fields.Float(
        string='Pending produce')
    product_route = fields.Selection(
        selection=[
            ('manufacture', 'Manufacture'),
            ('buy', 'Buy')],
        string='Product route')
    level = fields.Integer(
        string='Level')


class WizMrpSimulationBuyLine(models.TransientModel):
    _name = 'wiz.mrp.simulation.buy.line'
    _description = 'Simulation buy lines'

    name = fields.Char(
        string='Empty')
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product')
    qty_pending_buy = fields.Float(
        string='Quantity pending buy')
    buy_simulation_id = fields.Many2one(
        comodel_name='wiz.mrp.simulation',
        string='Buy simulation')


class WizMrpSimulationManufactureLine(models.TransientModel):
    _name = 'wiz.mrp.simulation.manufacture.line'
    _description = 'Simulation manufacture lines'

    name = fields.Char(
        string='Empty')
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product')
    qty_pending_produce = fields.Float(
        string='Quantity pending produce')
    manufacture_simulation_id = fields.Many2one(
        comodel_name='wiz.mrp.simulation',
        string='Manufacture simulation')
