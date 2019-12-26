# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.


# from osv import osv
# from osv import fields
# import decimal_precision as dp
# from tools.translate import _
# import time

from openerp import models, fields, api, exceptions, _
import openerp.addons.decimal_precision as dp


class SimulationCost(models.Model):
    _name = 'simulation.cost'
    _description = 'Simulation Costs'
   
    simulation_number = fields.Char(
        string='Serial',
        size=64)
    name = fields.Char(
        string='Description/Name',
        size=250,
        required=True,
        attrs={'readonly':[('historical_ok','=',True)]})
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer')
    historical_date = fields.Datetime(
        string='Historical Date',
        readonly=True)
    historical_ok = fields.Boolean(
        string='Historical OK')
    overhead_costs = fields.Float(
        string='Overhead Costs',
        digits_compute=dp.get_precision('Purchase Price'))
    purchase_insale = fields.Boolean(
        string='Copy Purchase information in Sale information',
        default=True)
    purchase_cost_lines_ids = fields.One2many(
        comodel_name='simulation.cost.line',
        inverse_name='simulation_cost_id',
        string='Purchase Lines',
        domain=[('type_cost','=','Purchase')],
        attrs={'readonly':[('historical_ok','=',True)]})
    investment_cost_lines_ids = fields.One2many(
        comodel_name='simulation.cost.line',
        inverse_name='simulation_cost_id',
        string='Investment Lines',
        domain=[('type_cost','=','Investment')],
        attrs={'readonly':[('historical_ok','=',True)]})
    subcontracting_cost_lines_ids = fields.One2many(
        comodel_name='simulation.cost.line',
        inverse_name='simulation_cost_id',
        string='Subcontracting Lines',
        domain=[('type_cost','=','Subcontracting Services')],
        attrs={'readonly':[('historical_ok','=',True)]})
    task_cost_lines_ids = fields.One2many(
        comodel_name='simulation.cost.line',
        inverse_name='simulation_cost_id',
        string='Internal Task Lines',
        domain=[('type_cost','=','Task')],
        attrs={'readonly':[('historical_ok','=',True)]})
    others_cost_lines_ids = fields.One2many(
        comodel_name='simulation.cost.line',
        inverse_name='simulation_cost_id',
        string='Others Lines',
        domain=[('type_cost', '=','Others')],
        attrs={'readonly':[('historical_ok','=',True)]})
    ### Total compras, ventas, beneficio para tipo coste purchase
    subtotal1_purchase = fields.Float(
        string='Total Purchase',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    subtotal1_sale = fields.Float(
        string='Total Sale',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    benefit1 = fields.Float(
        string='Total Benefit',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    ### Total compras, ventas, beneficio para tipo coste investment
    subtotal2_purchase = fields.float(
        string='Total Purchase',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    subtotal2_sale = fields.Float(
        string='Total Sale',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    benefit2 = fields.Float(
        string='Total Benefit',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    ### Total compras, ventas, beneficio para tipo coste subcontrating
    subtotal3_purchase = fields.float(
        string='Total Purchase',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    subtotal3_sale = fields.float(
        string='Total Sale',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    benefit3 = fields.Float(
        string='Total Benefit',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    ### Total compras, ventas, beneficio para tipo coste task
    subtotal4_purchase = fields.float(
        string='Total Purchase',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    subtotal4_sale = fields.Float(
        string='Total Sale',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    benefit4 = fields.float(
        string='Total Benefit',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    ### Total compras, ventas, beneficio para tipo coste others
    subtotal5_purchase = fields.Float(
        string='Total Purchase',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    subtotal5_sale = fields.Float(
        string='Total Sale',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    benefit5 = fields.Float(
        string='Total Benefit',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    ### Campos para los totales de la última pestaña
    subtotal1t_purchase = fields.Float(
        string='Total Purchase',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    subtotal1t_sale = fields.Float(
        string='Total Sale',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    benefit1t = fields.Float(
        string='Total Benefit',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    subtotal2t_purchase = fields.Float(
        string='Total Purchase',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    subtotal2t_sale = fields.Float(
        string='Total Sale',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    benefit2t = fields.Float(
        string='Total Benefit',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    subtotal3t_purchase = fields.Float(
        string='Total Purchase',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    subtotal3t_sale = fields.Float(
        string='Total Sale',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    benefit3t = fields.Float(
        string='Total Benefit',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    subtotal4t_purchase = fields.Float(
        string='Total Purchase',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    subtotal4t_sale = fields.float(
        string='Total Sale',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    benefit4t = fields.Float(
        string='Total Benefit',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    subtotal5t_purchase = fields.Float(
        string='Total Purchase',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    subtotal5t_sale = fields.Float(
        string='Total Sale',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    benefit5t = fields.float(
        string='Total Benefit',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    # Total Costes
    total_costs = fields.float(
        string='TOTAL COSTS',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    # Total Ventas
    total_sales = fields.float(
        string='TOTAL SALES',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    # Total Beneficios
    total_benefits = fields.Float(
        string='TOTAL BENEFITS',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    # Total amortizaciones
    total_amortizations = fields.Float(
        string='Total Amortizations',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    # Total indirectos
    total_indirects = fields.Float(
        string='Total Indirects',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    # Total amortizaciones + indirectos
    total_amort_indirects = fields.Float(
        string='TOTAL',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    # Gastos Generales
    total_overhead_costs = fields.Float(
        string='Overhead_costs',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    # Total
    total = fields.Float(
        string='TOTAL',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    # Precio Neto
    net_cost = fields.Float(
        string='Net Cost',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    # Porcentaje Precio Neto
    net_cost_percentage = fields.Float(
        string='Net Cost %',
        digits=(3,2),
        readonly=True)
    # Margen Bruto
    gross_margin = fields.Float(
        string='Gross Margin',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    # Porcentaje Margen Bruto
    gross_margin_percentage = fields.Float(
        string='Gross Margin %',
        digits=(3,2),
        readonly=True)
    # Margen de Contribución
    contribution_margin = fields.Float(
        string='Contribution Margin',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    # Porcentaje Margen Contribucion
    contribution_margin_percentage = fields.Float(
        string='Contribution Margin %',
        digits=(3,2),
        readonly=True)
    # Margen Neto
    net_margin = fields.Float(
        string='Net Margin',
        readonly=True,
        digits_compute=dp.get_precision('Purchase Price'))
    # Porcentaje Margen Neto
    net_margin_percentage = fields.Float(
        string='Net Margin %',
        digits=(3,2),
        readonly=True)
    # Pedidos de Venta
    sale_order_ids = fields.Many2many(
        comodel_name='sale.order',
        relation='simucost_saleorder_rel',
        column1='simulation_cost_id',
        column2='sale_order_id',
        string='Sale Orders',
        readonly=True)
    # Proyectos
    project_ids = fields.One2many(
        comodel_name='project.project',
        reverse_name='simulation_cost_id',
        string='Projects')
    # Subproyectos
    subproject_ids = fields.One2many(
        comodel_name='project.project',
        reverse_name='simulation_cost_id2',
        string='Subprojects'),
    # Generar Pedido de venta por productos de lineas de simulacion
    generate_by_line = fields.Boolean(
        string='Generate by line'),
    # WORKFLOW DE LA SIMULACION DEL COSTE
    state = fields.Selection([
        ('draft', 'Draft'),
        ('accepted', 'Accepted'),
        ('canceled', 'Canceled')],
        string='State',
        readonly=True,
        default='draft')

    @api.multi
    def create(self, cr, uid, data, context=None):
        seria = self.env['ir.sequence'].get('cost.serial'),
        serial = seria[0]
        data.update({'simulation_number': serial})
        return super(SimulationCost, self).create(data)
    
    @api.one
    def unlink(self, cr, uid, ids, context=None):
        if self.sale_order_ids:
            raise exceptions.Warning(
                _('Invalid action !'),
                _('This Simulation Costs Have Associated Sales Orders'))
        self.unlink(self)
        return True
   
    ### BOTÓN RECALCULAR TOTALES, este boton está en todas las pestañas
    @api.one
    def button_recalculation(self):
        ### Leo el Objeto Coste
        # simulation_cost = self.browse(cr, uid, ids[0])
        ### valido que no esté historificado ya
        if self.historical_ok:
            raise exceptions.Warning(
                _('Error'),
                _('This cost simulation have Historical'))
        
        subtotal_purchase_costs = 0.0
        subtotal_purchase_sales = 0.0
        subtotal_purchase_benefit = 0.0
        subtotal_investment_costs = 0.0
        subtotal_investment_sales = 0.0
        subtotal_investment_benefit = 0.0
        subtotal_subcontracting_costs = 0.0
        subtotal_subcontracting_sales = 0.0
        subtotal_subcontracting_benefit = 0.0
        subtotal_task_costs = 0.0
        subtotal_task_sales = 0.0
        subtotal_task_benefit = 0.0
        subtotal_others_costs = 0.0
        subtotal_others_sales = 0.0
        subtotal_others_benefit = 0.0
        total_costs = 0.0
        total_sales = 0.0
        total_benefit = 0.0
        total_amortizations = 0.0
        total_indirects = 0.0
        total_amort_indirects = 0.0
        subtotal_net_cost = 0.0
        subtotal_gross_margin = 0.0
        subtotal_contribution_margin = 0.0
        subtotal_net_margin = 0.0
        total_net_cost = 0.0
        total_gross_margin = 0.0
        total_contribution_margin = 0.0
        total_net_margin = 0.0
        net_cost_percentage = 0.0
        gross_margin_percentage = 0.0
        contribution_margin_percentage = 0.0
        net_margin_percentage = 0.0
        total_overhead_costs = 0.0
        total = 0.0
        #
        ### trato todas las líneas de tipo "PURCHASE"
        for cost_line in self.purchase_cost_lines_ids:
            ### Calculo el total de compras y el total de ventas
            subtotal_purchase_costs = subtotal_purchase_costs + cost_line.subtotal_purchase
            subtotal_purchase_sales = subtotal_purchase_sales + cost_line.subtotal_sale
            #
            ### Sumo importes para Precio Neto, Margen Bruto, Margen de Contribución, Margen Neto    
            if cost_line.type2:
                if cost_line.type2 == 'variable':       
                    if cost_line.type3:
                        if cost_line.type3 == 'marketing' or cost_line.type3 == 'sale':
                            subtotal_net_cost = subtotal_net_cost + \
                                                cost_line.subtotal_purchase
                        else:
                            if cost_line.type3 == 'production':
                                subtotal_gross_margin = \
                                    subtotal_gross_margin + \
                                    cost_line.subtotal_purchase
                else:
                    if cost_line.type2 == 'fixed':
                        if cost_line.type3:
                            if cost_line.type3 == 'production':
                                subtotal_contribution_margin = \
                                    subtotal_contribution_margin + \
                                    cost_line.subtotal_purchase
                            else:
                                if cost_line.type3 == 'sale' or \
                                                cost_line.type3 == \
                                                'marketing' or \
                                                cost_line.type3 == \
                                                'structureexpenses' or \
                                                cost_line.type3 == \
                                                'generalexpenses':
                                    subtotal_net_margin = \
                                        subtotal_net_margin + \
                                        cost_line.subtotal_purchase
            
        subtotal_purchase_benefit = subtotal_purchase_sales - \
                                    subtotal_purchase_costs
        ### trato todas las líneas de tipo "INVESTMENT"
        for cost_line in self.investment_cost_lines_ids:
            ### Calculo el total de compras y el total de ventas
            subtotal_investment_costs = subtotal_investment_costs + \
                                        cost_line.subtotal_purchase
            subtotal_investment_sales = subtotal_investment_sales + \
                                        cost_line.subtotal_sale
            
        subtotal_investment_benefit = subtotal_investment_sales - \
                                      subtotal_investment_costs
        ### trato todas las líneas de tipo "SUBCONTRACTING"
        for cost_line in self.subcontracting_cost_lines_ids:
            ### Calculo el total de compras y el total de ventas
            subtotal_subcontracting_costs = subtotal_subcontracting_costs + \
                                            cost_line.subtotal_purchase
            subtotal_subcontracting_sales = subtotal_subcontracting_sales + \
                                            cost_line.subtotal_sale
            ### Sumo importes para Precio Neto, Margen Bruto, Margen de Contribución, Margen Neto
            if cost_line.type2:
                if cost_line.type2 == 'variable':       
                    if cost_line.type3:
                        if cost_line.type3 == 'marketing' or cost_line.type3\
                                == 'sale':
                            subtotal_net_cost = subtotal_net_cost + \
                                                cost_line.subtotal_purchase
                        else:
                            if cost_line.type3 == 'production':
                                subtotal_gross_margin = \
                                    subtotal_gross_margin + \
                                    cost_line.subtotal_purchase
                else:
                    if cost_line.type2 == 'fixed':
                        if cost_line.type3:
                            if cost_line.type3 == 'production':
                                subtotal_contribution_margin = \
                                    subtotal_contribution_margin + \
                                    cost_line.subtotal_purchase
                            else:
                                if cost_line.type3 == 'sale' or \
                                                cost_line.type3 == \
                                                'marketing' or \
                                                cost_line.type3 == \
                                                'structureexpenses' or \
                                                cost_line.type3 == \
                                                'generalexpenses':
                                    subtotal_net_margin = \
                                        subtotal_net_margin + \
                                        cost_line.subtotal_purchase
        subtotal_subcontracting_benefit = subtotal_subcontracting_sales - \
                                          subtotal_subcontracting_costs
        ### trato todas las líneas de tipo "TASK"
        for cost_line in self.task_cost_lines_ids:
            ### Calculo el total de compras y el total de ventas
            subtotal_task_costs = subtotal_task_costs + \
                                  cost_line.subtotal_purchase
            subtotal_task_sales = subtotal_task_sales + cost_line.subtotal_sale
            ### Sumo los costes de amortización, y los costes indirectos
            total_amortizations = total_amortizations + \
                                  cost_line.amortization_cost
            total_indirects = total_indirects + cost_line.indirect_cost
            ### Sumo importes para Precio Neto, Margen Bruto, Margen de Contribución, Margen Neto
            if cost_line.type2:
                if cost_line.type2 == 'variable':       
                    if cost_line.type3:
                        if cost_line.type3 == 'marketing' or cost_line.type3\
                                == 'sale':
                            subtotal_net_cost = subtotal_net_cost + \
                                                cost_line.subtotal_purchase
                        else:
                            if cost_line.type3 == 'production':
                                subtotal_gross_margin = \
                                    subtotal_gross_margin + \
                                    cost_line.subtotal_purchase
                else:
                    if cost_line.type2 == 'fixed':
                        if cost_line.type3:
                            if cost_line.type3 == 'production':
                                subtotal_contribution_margin = \
                                    subtotal_contribution_margin + \
                                    cost_line.subtotal_purchase
                            else:
                                if cost_line.type3 == 'sale' or \
                                                cost_line.type3 == \
                                                'marketing' or \
                                                cost_line.type3 == \
                                                'structureexpenses' or \
                                                cost_line.type3 == \
                                                'generalexpenses':
                                    subtotal_net_margin = \
                                        subtotal_net_margin + \
                                        cost_line.subtotal_purchase
        subtotal_task_benefit = subtotal_task_sales - subtotal_task_costs
        ### trato todas las líneas de tipo "OTHERS"
        for cost_line in self.others_cost_lines_ids:
            ### Calculo el total de compras y el total de ventas
            subtotal_others_costs = subtotal_others_costs + \
                                    cost_line.subtotal_purchase
            subtotal_others_sales = subtotal_others_sales + \
                                    cost_line.subtotal_sale
            ### Sumo los costes de amortización, y los costes indirectos
            total_amortizations = total_amortizations + \
                                  cost_line.amortization_cost
            total_indirects = total_indirects + cost_line.indirect_cost
            # Sumo importes para Precio Neto, Margen Bruto, Margen de
            # Contribución, Margen Neto
            if cost_line.type2:
                if cost_line.type2 == 'variable':       
                    if cost_line.type3:
                        if cost_line.type3 == 'marketing' or cost_line.type3\
                                == 'sale':
                            subtotal_net_cost = subtotal_net_cost + \
                                                cost_line.subtotal_purchase
                        else:
                            if cost_line.type3 == 'production':
                                subtotal_gross_margin = \
                                    subtotal_gross_margin + \
                                    cost_line.subtotal_purchase
                else:
                    if cost_line.type2 == 'fixed':
                        if cost_line.type3:
                            if cost_line.type3 == 'production':
                                subtotal_contribution_margin = \
                                    subtotal_contribution_margin + \
                                    cost_line.subtotal_purchase
                            else:
                                if cost_line.type3 == 'sale' or \
                                                 cost_line.type3 == \
                                                 'marketing' or \
                                                 cost_line.type3 == \
                                                 'structureexpenses' or \
                                                 cost_line.type3 == \
                                                 'generalexpenses':
                                    subtotal_net_margin = \
                                        subtotal_net_margin + \
                                        cost_line.subtotal_purchase
        subtotal_others_benefit = subtotal_others_sales - subtotal_others_costs
        ### Calculo totales generales
        total_costs = subtotal_purchase_costs + \
                      subtotal_subcontracting_costs + subtotal_task_costs + \
                      subtotal_others_costs
        total_sales = subtotal_purchase_sales + subtotal_subcontracting_sales +\
                      subtotal_task_sales + subtotal_others_sales
        total_benefit = subtotal_purchase_benefit +\
                        subtotal_subcontracting_benefit +\
                        subtotal_task_benefit +\
                        subtotal_others_benefit
        ### Calculo el total de amortizaciones + costes indirectos
        total_amort_indirects = total_amortizations + total_indirects
        #
        ### Calculo Precio Neto, Margen Bruto, Margen de Contribución, Margen Neto
        total_net_cost = total_sales - subtotal_net_cost
        total_gross_margin = total_net_cost - subtotal_gross_margin        
        total_contribution_margin = total_gross_margin - \
                                    subtotal_contribution_margin - \
                                    total_indirects
        total_net_margin = total_contribution_margin - subtotal_net_margin -\
                           total_amortizations - total_costs
        ### Calculo los porcentajes de los importes anteriores
        if total_net_cost > 0 and total_sales > 0:
            net_cost_percentage = (total_net_cost * 100) / total_sales
        if total_gross_margin > 0 and total_sales > 0:
            gross_margin_percentage = (total_gross_margin * 100) / total_sales
        if total_contribution_margin > 0 and total_sales > 0:
            contribution_margin_percentage = (total_contribution_margin * 100) / total_sales
        if total_net_margin > 0 and total_sales > 0:
            net_margin_percentage = (total_net_margin * 100) / total_sales  
        
        if self.overhead_costs:
            if self.overhead_costs > 0:
                if total_amort_indirects > 0 and total_costs > 0:
                    total_overhead_costs = (self.overhead_costs * (
                        total_amort_indirects + total_costs)) / 100

        total = total_indirects + total_costs + total_overhead_costs        
        ### Modifico el Objeto con los totales
        self.write({
            'subtotal1_purchase': subtotal_purchase_costs,
            'subtotal1_sale': subtotal_purchase_sales,
            'benefit1': subtotal_purchase_benefit,
            'subtotal1t_purchase': subtotal_purchase_costs,
            'subtotal1t_sale': subtotal_purchase_sales,
            'benefit1t': subtotal_purchase_benefit,
            'subtotal2_purchase': subtotal_investment_costs,
            'subtotal2_sale': subtotal_investment_sales,
            'benefit2': subtotal_investment_benefit,
            'subtotal2t_purchase': subtotal_investment_costs,
            'subtotal2t_sale': subtotal_investment_sales,
            'benefit2t': subtotal_investment_benefit,
            'subtotal3_purchase': subtotal_subcontracting_costs,
            'subtotal3_sale': subtotal_subcontracting_sales,
            'benefit3': subtotal_subcontracting_benefit,
            'subtotal3t_purchase': subtotal_subcontracting_costs,
            'subtotal3t_sale': subtotal_subcontracting_sales,
            'benefit3t': subtotal_subcontracting_benefit,
            'subtotal4_purchase': subtotal_task_costs,
            'subtotal4_sale': subtotal_task_sales,
            'benefit4': subtotal_task_benefit,
            'subtotal4t_purchase': subtotal_task_costs,
            'subtotal4t_sale': subtotal_task_sales,
            'benefit4t': subtotal_task_benefit,
            'subtotal5_purchase': subtotal_others_costs,
            'subtotal5_sale': subtotal_others_sales,
            'benefit5': subtotal_others_benefit,
            'subtotal5t_purchase': subtotal_others_costs,
            'subtotal5t_sale': subtotal_others_sales,
            'benefit5t': subtotal_others_benefit,
            'total_costs': total_costs,
            'total_sales': total_sales,
            'total_benefits': total_benefit,
            'total_amortizations': total_amortizations,
            'total_indirects': total_indirects,
            'total_amort_indirects': total_amort_indirects,
            'total_overhead_costs': total_overhead_costs,
            'total':total,
            'net_cost': total_net_cost,
            'net_cost_percentage': net_cost_percentage,
            'gross_margin': total_gross_margin,
            'gross_margin_percentage': gross_margin_percentage,
            'contribution_margin': total_contribution_margin,
            'contribution_margin_percentage': contribution_margin_percentage,
            'net_margin': total_net_margin,
            'net_margin_percentage': net_margin_percentage
        })
        return True
    
    @api.multi
    def button_confirm_create_sale_order(self):
        val = True
        for simulation in self:
            # context.update({'active_id': simulation.id})
            #llamada al wizard
            val = {
                'name':'Confirm Create Sale Order',
                'type':'ir.actions.act_window',
                'res_model':'wiz.confirm.create.sale.order',
                'view_type':'form',
                'view_mode':'form',
                'nodestroy':True,
                'target':'new',
            }
        return val
    
    @api.one
    def button_create_sale_order(self):
        if self.historical_ok:
            raise exceptions.Warning(
                _('Error'),
                _('You can not generate one Sale Order from one Historical'))
        ### Para crear un pedido de venta, la simulación debe de tener
        ### asignada un cliente
        if not self.partner_id:
            raise exceptions.Warning(
                _('Customer Error'),
                _('You must assign a customer to the simulation'))
        ### Switch para saber si tengo que grabar SALE.ORDER
        grabar_sale_order = False
        ### T R A T O   L I N E A S   "PURCHASE" y las guardo en una tabla
        purchase_datas = {}
        general_datas = {}
        for cost_line in self.purchase_cost_lines_ids:
            ### Solo trato la línea si la linea de simulación de coste
            ### NO está asociada a ninguna línea de pedido
            if not cost_line.sale_order_line_id:
                if not cost_line.product_id:
                    raise exceptions.Warning(
                        _('Create Sale Order Error'),
                        _('On a line of purchase lines, needed to define a '
                          'purchase product: '))
                else:
                    if not cost_line.product_sale_id:
                        raise exceptions.Warning(
                            _('Create Sale Order Error'),
                            _('On a line of purchase lines, needed to define a'
                              ' sale product, cost product: ' + str(
                                cost_line.product_id.name)))
                    else:
                        grabar_sale_order = True
                        w_generation_type = 0
                        if self.generate_by_line == True:
                            w_generation_type = 1
                        else:
                            if not cost_line.template_id:
                                w_generation_type = 1
                            else:
                                if not cost_line.template_id.template_product_id:
                                    w_generation_type = 1
                                else:
                                    w_generation_type = 2
                                    
                        if w_generation_type == 1:           
                            ### Si el producto existe en el array sumo su precio de venta
                            encontrado = 0
                            subtotal_sale = 0
                            for data in purchase_datas:        
                                datos_array = purchase_datas[data]
                                product_sale_id = datos_array['product_sale_id']
                                subtotal_sale = datos_array['subtotal_sale']
                                lines_ids = datos_array['lines_ids']             
                                if product_sale_id == cost_line.product_sale_id.id:
                                    # Si encuentro el producto de la línea en el array 
                                    encontrado = 1
                                    # incremento el importe de la venta
                                    subtotal_sale = subtotal_sale + cost_line.subtotal_sale
                                    # Añado el id de la linea de coste al último parámetro del array
                                    lines_ids.append(cost_line.id)
                                    purchase_datas[data].update({
                                        'subtotal_sale':subtotal_sale,
                                        'lines_ids': lines_ids})
                            ### Si no he encontrado el producto en el array, lo inserto
                            ### en la última posición. En el último parámetro se guarda una lista
                            ### con todos los id de las líneas de la simulacion de costes
                            ### que han participado en la creación de la
                            # línea del pedido de venta
                            if encontrado == 0:
                                purchase_datas[(
                                    cost_line.product_sale_id.id)] = {
                                    'product_sale_id': cost_line.product_sale_id.id,
                                    'subtotal_sale': cost_line.subtotal_sale,
                                    'name': cost_line.product_sale_id.name,
                                    'lines_ids': [cost_line.id]}
                        else:
                            ### Si el producto existe en el array sumo su precio de venta
                            encontrado = 0
                            subtotal_sale = 0
                            for data in general_datas:        
                                datos_array = general_datas[data]
                                product_sale_id = datos_array['product_sale_id']
                                subtotal_sale = datos_array['subtotal_sale']
                                lines_ids = datos_array['lines_ids']
                                if product_sale_id == cost_line.template_id.template_product_id.id:
                                    # Si encuentro el producto de la línea en el array 
                                    encontrado = 1
                                    # incremento el importe de la venta
                                    subtotal_sale = subtotal_sale + cost_line.subtotal_sale
                                    # Añado el id de la linea de coste al último parámetro del array
                                    lines_ids.append(cost_line.id)
                                    general_datas[data].update({
                                        'subtotal_sale':subtotal_sale,
                                        'lines_ids': lines_ids})
                            ### Si no he encontrado el producto en el array, lo inserto
                            ### en la última posición. En el último parámetro se guarda una lista
                            ### con todos los id de las líneas de la simulacion de costes
                            ### que han participado en la creación de la línea lel pedido de venta
                            if encontrado == 0:
                                general_datas[(cost_line.template_id.template_product_id.id)] = {'product_sale_id': cost_line.template_id.template_product_id.id, 'subtotal_sale': cost_line.subtotal_sale, 'name': cost_line.template_id.template_product_id.name, 'lines_ids': [cost_line_id.id]}
       ### T R A T O   L I N E A S   "INVESTMENT" y as guardo en una tabla
        investment_datas = {}
        for cost_line in self.investment_cost_lines_ids:
            ### Solo trato la línea si la linea de simulación de coste
            ### NO está asociada a ninguna línea de pedido
            if not cost_line.sale_order_line_id:
                if not cost_line.product_id:
                    raise exceptions.Warning(
                        _('Create Sale Order Error'),
                        _('On a line of investment lines, needed to define a '
                          'purchase product'))
                else:
                    if not cost_line.product_sale_id:
                        raise exceptions.Warning(
                            _('Create Sale Order Error'),
                            _('On a line of investment lines, needed to define'
                              ' a sale product'))
                    else:  
                        grabar_sale_order = True
                        w_generation_type = 0
                        if self.generate_by_line == True:
                            w_generation_type = 1
                        else:
                            if not cost_line.template_id:
                                w_generation_type = 1
                            else:
                                if not cost_line.template_id.template_product_id:
                                    w_generation_type = 1
                                else:
                                    w_generation_type = 2
                                    
                        if w_generation_type == 1:           
                            ### Si el producto existe en el array sumo su precio de venta
                            encontrado = 0
                            subtotal_sale = 0
                            for data in investment_datas:        
                                datos_array = investment_datas[data]
                                product_sale_id = datos_array['product_sale_id']
                                subtotal_sale = datos_array['subtotal_sale']
                                lines_ids = datos_array['lines_ids']             
                                if product_sale_id == cost_line.product_sale_id.id:
                                    # Si encuentro el producto de la línea en el array 
                                    encontrado = 1
                                    # incremento el importe de la venta
                                    subtotal_sale = subtotal_sale + cost_line.subtotal_sale
                                    # Añado el id de la linea de coste al último parámetro del array
                                    lines_ids.append(cost_line.id)
                                    investment_datas[data].update({
                                        'subtotal_sale':subtotal_sale,
                                        'lines_ids': lines_ids})
                            ### Si no he encontrado el producto en el array, lo inserto
                            ### en la última posición. En el último parámetro se guarda una lista
                            ### con todos los id de las líneas de la simulacion de costes
                            ### que han participado en la creación de la línea lel pedido de venta
                            if encontrado == 0:
                                investment_datas[(cost_line.product_sale_id.id)] = {'product_sale_id': cost_line.product_sale_id.id, 'subtotal_sale': cost_line.subtotal_sale, 'name': cost_line.product_sale_id.name, 'lines_ids': [cost_line_id.id]} 

                        else:
                            ### Si el producto existe en el array sumo su precio de venta
                            encontrado = 0
                            subtotal_sale = 0
                            for data in general_datas:        
                                datos_array = general_datas[data]
                                product_sale_id = datos_array['product_sale_id']
                                subtotal_sale = datos_array['subtotal_sale']
                                lines_ids = datos_array['lines_ids']
                                if product_sale_id == cost_line.template_id.template_product_id.id:
                                    # Si encuentro el producto de la línea en el array 
                                    encontrado = 1
                                    # incremento el importe de la venta
                                    subtotal_sale = subtotal_sale + cost_line.subtotal_sale
                                    # Añado el id de la linea de coste al último parámetro del array
                                    lines_ids.append(cost_line.id)
                                    general_datas[data].update({
                                        'subtotal_sale':subtotal_sale,
                                        'lines_ids': lines_ids})
                            ### Si no he encontrado el producto en el array, lo inserto
                            ### en la última posición. En el último parámetro se guarda una lista
                            ### con todos los id de las líneas de la simulacion de costes
                            ### que han participado en la creación de la línea lel pedido de venta
                            if encontrado == 0:
                                general_datas[(cost_line.template_id.template_product_id.id)] = {'product_sale_id': cost_line.template_id.template_product_id.id, 'subtotal_sale': cost_line.subtotal_sale, 'name': cost_line.template_id.template_product_id.name, 'lines_ids': [cost_line_id.id]} 
        ### T R A T O   L I N E A S   "SUBCONTRACTING"
        subcontracting_datas = {}
        for cost_line in self.subcontracting_cost_lines_ids:
            ### Solo trato la línea si la linea de simulación de coste
            ### NO está asociada a ninguna línea de pedido
            #
            if not cost_line.sale_order_line_id:
                if not cost_line.product_id:
                    raise exceptions.Warning(
                        _('Create Sale Order Error'),
                        _('On a line of subcontracting lines, needed to '
                          'define a purchase product'))
                else:
                    if not cost_line.product_sale_id:
                        raise exceptions.Warning(
                            _('Create Sale Order Error'),
                            _('On a line of subcontracting lines, needed to '
                              'define a sale product'))
                    else:  
                        grabar_sale_order = True
                        w_generation_type = 0
                        if self.generate_by_line:
                            w_generation_type = 1
                        else:
                            if not cost_line.template_id:
                                w_generation_type = 1
                            else:
                                if not cost_line.template_id.template_product_id:
                                    w_generation_type = 1
                                else:
                                    w_generation_type = 2
                        if w_generation_type == 1:           
                            ### Si el producto existe en el array sumo su precio de venta
                            encontrado = 0
                            subtotal_sale = 0
                            for data in subcontracting_datas:        
                                datos_array = subcontracting_datas[data]
                                product_sale_id = datos_array['product_sale_id']
                                subtotal_sale = datos_array['subtotal_sale']
                                lines_ids = datos_array['lines_ids']             
                                if product_sale_id == cost_line.product_sale_id.id:
                                    # Si encuentro el producto de la línea en el array 
                                    encontrado = 1
                                    # incremento el importe de la venta
                                    subtotal_sale = subtotal_sale + cost_line.subtotal_sale
                                    # Añado el id de la linea de coste al último parámetro del array
                                    lines_ids.append(cost_line.id)
                                    subcontracting_datas[data].update({'subtotal_sale':subtotal_sale,
                                                                 'lines_ids': lines_ids})
                            ### Si no he encontrado el producto en el array, lo inserto
                            ### en la última posición. En el último parámetro se guarda una lista
                            ### con todos los id de las líneas de la simulacion de costes
                            ### que han participado en la creación de la línea lel pedido de venta
                            if encontrado == 0:
                                subcontracting_datas[(cost_line.product_sale_id.id)] = {'product_sale_id': cost_line.product_sale_id.id, 'subtotal_sale': cost_line.subtotal_sale, 'name': cost_line.product_sale_id.name, 'lines_ids': [cost_line_id.id]} 
                        else:
                            ### Si el producto existe en el array sumo su precio de venta
                            #
                            encontrado = 0
                            subtotal_sale = 0
                            for data in general_datas:        
                                datos_array = general_datas[data]
                                product_sale_id = datos_array['product_sale_id']
                                subtotal_sale = datos_array['subtotal_sale']
                                lines_ids = datos_array['lines_ids']
                                if product_sale_id == cost_line.template_id.template_product_id.id:
                                    # Si encuentro el producto de la línea en el array 
                                    encontrado = 1
                                    # incremento el importe de la venta
                                    subtotal_sale = subtotal_sale + cost_line.subtotal_sale
                                    # Añado el id de la linea de coste al último parámetro del array
                                    lines_ids.append(cost_line.id)
                                    general_datas[data].update({'subtotal_sale':subtotal_sale,
                                                                'lines_ids': lines_ids})
                            ### Si no he encontrado el producto en el array, lo inserto
                            ### en la última posición. En el último parámetro se guarda una lista
                            ### con todos los id de las líneas de la simulacion de costes
                            ### que han participado en la creación de la línea lel pedido de venta
                            if encontrado == 0:
                                general_datas[(cost_line.template_id.template_product_id.id)] = {'product_sale_id': cost_line.template_id.template_product_id.id, 'subtotal_sale': cost_line.subtotal_sale, 'name': cost_line.template_id.template_product_id.name, 'lines_ids': [cost_line_id.id]}
        ### T R A T O   L I N E A S   "TASK" 
        task_datas = {}
        for cost_line in self.task_cost_lines_ids:
            ### Solo trato la línea si la linea de simulación de coste
            ### NO está asociada a ninguna línea de pedido
            if not cost_line.sale_order_line_id:
                if not cost_line.product_id:
                    raise exceptions.Warning(
                        _('Create Sale Order Error'),
                        _('On a line of task lines, needed to define a '
                          'purchase product'))
                else:
                    if not cost_line.product_sale_id:
                        raise exceptions.Warning(
                            _('Create Sale Order Error'),
                            _('On a line of task lines, needed to define a '
                              'sale product'))
                    else:  
                        grabar_sale_order = True
                        w_generation_type = 0
                        if self.generate_by_line == True:
                            w_generation_type = 1
                        else:
                            if not cost_line.template_id:
                                w_generation_type = 1
                            else:
                                if not cost_line.template_id.template_product_id:
                                    w_generation_type = 1
                                else:
                                    w_generation_type = 2
                                    
                        if w_generation_type == 1:           
                            ### Si el producto existe en el array sumo su precio de venta
                            encontrado = 0
                            subtotal_sale = 0
                            for data in task_datas:        
                                datos_array = task_datas[data]
                                product_sale_id = datos_array['product_sale_id']
                                subtotal_sale = datos_array['subtotal_sale']
                                lines_ids = datos_array['lines_ids']             
                                if product_sale_id == cost_line.product_sale_id.id:
                                    # Si encuentro el producto de la línea en el array 
                                    encontrado = 1
                                    # incremento el importe de la venta
                                    subtotal_sale = subtotal_sale + cost_line.subtotal_sale
                                    # Añado el id de la linea de coste al último parámetro del array
                                    lines_ids.append(cost_line.id)
                                    task_datas[data].update({
                                        'subtotal_sale':subtotal_sale,
                                        'lines_ids': lines_ids})
                            ### Si no he encontrado el producto en el array, lo inserto
                            ### en la última posición. En el último parámetro se guarda una lista
                            ### con todos los id de las líneas de la simulacion de costes
                            ### que han participado en la creación de la línea lel pedido de venta
                            if encontrado == 0:
                                task_datas[(cost_line.product_sale_id.id)] = {'product_sale_id': cost_line.product_sale_id.id, 'subtotal_sale': cost_line.subtotal_sale, 'name': cost_line.product_sale_id.name, 'lines_ids': [cost_line_id.id]} 
                        else:
                            ### Si el producto existe en el array sumo su precio de venta
                            encontrado = 0
                            subtotal_sale = 0
                            for data in general_datas:        
                                datos_array = general_datas[data]
                                product_sale_id = datos_array['product_sale_id']
                                subtotal_sale = datos_array['subtotal_sale']
                                lines_ids = datos_array['lines_ids']
                                if product_sale_id == cost_line.template_id.template_product_id.id:
                                    # Si encuentro el producto de la línea en el array 
                                    encontrado = 1
                                    # incremento el importe de la venta
                                    subtotal_sale = subtotal_sale + cost_line.subtotal_sale
                                    # Añado el id de la linea de coste al último parámetro del array
                                    lines_ids.append(cost_line.id)
                                    general_datas[data].update({
                                        'subtotal_sale':subtotal_sale,
                                        'lines_ids': lines_ids})
                            ### Si no he encontrado el producto en el array, lo inserto
                            ### en la última posición. En el último parámetro se guarda una lista
                            ### con todos los id de las líneas de la simulacion de costes
                            ### que han participado en la creación de la línea lel pedido de venta
                            if encontrado == 0:
                                general_datas[(cost_line.template_id.template_product_id.id)] = {'product_sale_id': cost_line.template_id.template_product_id.id, 'subtotal_sale': cost_line.subtotal_sale, 'name': cost_line.template_id.template_product_id.name, 'lines_ids': [cost_line_id.id]} 
        #
        ### T R A T O   L I N E A S   "OTHERS"
        others_datas = {}
        for cost_line in self.others_cost_lines_ids:
            ### Solo trato la línea si la linea de simulación de coste
            ### NO está asociada a ninguna línea de pedido
            if not cost_line.sale_order_line_id:
                if not cost_line.product_id:
                    raise exceptions.Warning(
                        _('Create Sale Order Error'),
                        _('On a line of others lines, needed to define a '
                          'purchase product'))
                else:
                    if not cost_line.product_sale_id:
                        raise exceptions.Warning(
                            _('Create Sale Order Error'),
                            _('On a line of others lines, needed to define a '
                              'sale product'))
                    else:  
                        grabar_sale_order = True
                        w_generation_type = 0
                        if self.generate_by_line == True:
                            w_generation_type = 1
                        else:
                            if not cost_line.template_id:
                                w_generation_type = 1
                            else:
                                if not cost_line.template_id.template_product_id:
                                    w_generation_type = 1
                                else:
                                    w_generation_type = 2
                                    
                        if w_generation_type == 1:           
                            ### Si el producto existe en el array sumo su precio de venta
                            encontrado = 0
                            subtotal_sale = 0
                            for data in others_datas:        
                                datos_array = others_datas[data]
                                product_sale_id = datos_array['product_sale_id']
                                subtotal_sale = datos_array['subtotal_sale']
                                lines_ids = datos_array['lines_ids']             
                                if product_sale_id == cost_line.product_sale_id.id:
                                    # Si encuentro el producto de la línea en el array 
                                    encontrado = 1
                                    # incremento el importe de la venta
                                    subtotal_sale = subtotal_sale + cost_line.subtotal_sale
                                    # Añado el id de la linea de coste al último parámetro del array
                                    lines_ids.append(cost_line.id)
                                    others_datas[data].update({
                                        'subtotal_sale':subtotal_sale,
                                        'lines_ids': lines_ids})
                            ### Si no he encontrado el producto en el array, lo inserto
                            ### en la última posición. En el último parámetro se guarda una lista
                            ### con todos los id de las líneas de la simulacion de costes
                            ### que han participado en la creación de la línea lel pedido de venta
                            if encontrado == 0:
                                others_datas[(cost_line.product_sale_id.id)] = {'product_sale_id': cost_line.product_sale_id.id, 'subtotal_sale': cost_line.subtotal_sale, 'name': cost_line.product_sale_id.name, 'lines_ids': [cost_line_id.id]} 
                        else:
                            ### Si el producto existe en el array sumo su precio de venta
                            encontrado = 0
                            subtotal_sale = 0
                            for data in general_datas:        
                                datos_array = general_datas[data]
                                product_sale_id = datos_array['product_sale_id']
                                subtotal_sale = datos_array['subtotal_sale']
                                lines_ids = datos_array['lines_ids']
                                if product_sale_id == cost_line.template_id.template_product_id.id:
                                    # Si encuentro el producto de la línea en el array 
                                    encontrado = 1
                                    # incremento el importe de la venta
                                    subtotal_sale = subtotal_sale + cost_line.subtotal_sale
                                    # Añado el id de la linea de coste al último parámetro del array
                                    lines_ids.append(cost_line.id)
                                    general_datas[data].update({
                                        'subtotal_sale':subtotal_sale,
                                        'lines_ids': lines_ids})
                            ### Si no he encontrado el producto en el array, lo inserto
                            ### en la última posición. En el último parámetro se guarda una lista
                            ### con todos los id de las líneas de la simulacion de costes
                            ### que han participado en la creación de la línea lel pedido de venta
                            if encontrado == 0:
                                general_datas[(cost_line.template_id.template_product_id.id)] = {'product_sale_id': cost_line.template_id.template_product_id.id, 'subtotal_sale': cost_line.subtotal_sale, 'name': cost_line.template_id.template_product_id.name, 'lines_ids': [cost_line_id.id]}
        ### Si noy hay lineas para grabar, muestro el error
        if not grabar_sale_order:
            raise exceptions.Warning(
                _('Error'),
                _('No Cost Lines found to Treat')) 
        ### G R A B O   SALER.ORDER  
        ### CREO EL OBJETO SALE.ORDER
        # sale_order_obj = self.env['sale.order']
        ### Cojo los datos del cliente
        addr = self.env['res.partner'].address_get(
            [self.partner_id.id],
            ['delivery', 'invoice', 'contact'])
        val = {
            'partner_id': self.partner_id.id,
            'partner_invoice_id': addr['invoice'],
            'partner_order_id': addr['contact'],
            'partner_shipping_id': addr['delivery'],
            'simulation_cost_ids':  [( 6, 0, [self.id])],
            'payment_term': self.partner_id.property_payment_term and \
                self.partner_id.property_payment_term.id or False,
            'fiscal_position': self.partner_id.property_account_position and \
                self.partner_id.property_account_position.id or False,
            'user_id': self.partner_id.user_id and 
                       self.partner_id.user_id.id or self.env.user,
            'pricelist_id' : self.partner_id.property_product_pricelist and \
                self.partner_id.property_product_pricelist.id or False
        }
        ### Grabo SALE.ORDER    
        sale_order_id = self.env['sale.order'].create(val)
        ### CREO EL OBJETO SALE.ORDER.LINE PARA CUANDO GENERO LINEAS DE PEDIDOS DE VENTA CON EL PRODUCTO DE LA PLANTILLA
        for data in general_datas:
            #Cojo los datos del array
            datos_array = general_datas[data]
            product_sale_id = datos_array['product_sale_id']
            subtotal_sale = datos_array['subtotal_sale'] 
            name = datos_array['name']
            lines_ids = datos_array['lines_ids']     
            context = {}
            lang = context.get('lang',False)
            context = {'lang': lang, 'partner_id': self.partner_id.id}     
            product_obj = self.env['product.product'].browse(product_sale_id)  
            tax_id = self.env['account.fiscal.position'].map_tax(
                self.partner_id.property_account_position,
                product_obj.taxes_id)


            values_line = {
                'product_id': product_sale_id,
                'type': 'make_to_order',
                'order_id': sale_order_id,            
                'name': name,
                'product_uom': product_obj.uom_id.id,
                'price_unit': subtotal_sale,
                'tax_id': [( 6, 0, tax_id)],
                'simulation_cost_line_ids': [( 6, 0, lines_ids)]
            }
            self.env['sale.order.line'].create(values_line)
        #
        ### CREO EL OBJETO SALE.ORDER.LINE PARA PURCHASE LINES
        for data in purchase_datas:
            #Cojo los datos del array
            datos_array = purchase_datas[data]
            lines_ids = datos_array['lines_ids']     
            context = {}
            lang = context.get('lang',False)
            context = {'lang': lang, 'partner_id': self.partner_id.id}     
            product_id = self.env['product.product'].browse(
                datos_array['product_sale_id'])  
            tax_id = self.env['account.fiscal.position'].map_tax(
                self.partner_id.property_account_position, product_id.taxes_id)
            values_line = {
                'type': 'make_to_order',
                'order_id': sale_order_id,            
                'product_id': purchase_datas[data]['product_sale_id'],
                'name': purchase_datas[data]['name'],
                'product_uom': product_id.uom_id.id,
                'price_unit': purchase_datas[data]['subtotal_sale'],
                'tax_id': [( 6, 0, tax_id)],
                'simulation_cost_line_ids': [( 6, 0, lines_ids)]
            }
            self.env['sale.order.line'].create(values_line)   
        ### CREO EL OBJETO SALE.ORDER.LINE PARA INVESTMENT LINES
        for data in investment_datas:
            #Cojo los datos del array
            datos_array = investment_datas[data]
            product_sale_id = datos_array['product_sale_id']
            subtotal_sale = datos_array['subtotal_sale'] 
            name = datos_array['name']
            lines_ids = datos_array['lines_ids']       
            context = {}
            lang = context.get('lang',False)
            context = {'lang': lang, 'partner_id': self.partner_id.id}         
            product_id = product_obj.browse(product_sale_id)
            tax_id = self.env['account.fiscal.position'].map_tax(
                self.partner_id.property_account_position, product_obj.taxes_id)
            pedido_linea_obj = self.pool.get('sale.order.line')
            values_line = {
                'product_id': product_sale_id,
                'order_id': sale_order_id,   
                'type': 'make_to_order',
                'name': name,
                'product_uom': product_obj.uom_id.id,
                'price_unit': subtotal_sale,
                'tax_id': [( 6, 0, tax_id)],
                'simulation_cost_line_ids': [( 6, 0, lines_ids)]}
            self.env['sale.order.line'].create(values_line)  
        ### CREO EL OBJETO SALE.ORDER.LINE PARA SUBCONTRACTING LINES
        for data in subcontracting_datas:
            #Cojo los datos del array
            datos_array = subcontracting_datas[data]
            product_sale_id = datos_array['product_sale_id']
            subtotal_sale = datos_array['subtotal_sale'] 
            name = datos_array['name']
            lines_ids = datos_array['lines_ids']       
            context = {}
            lang = context.get('lang',False)
            context = {'lang': lang, 'partner_id': self.partner_id.id}         
            product_obj = self.pool.get('product.product')
            product_obj = self.env['product.product'].browse(product_sale_id)
            tax_id = self.env['account.fiscal.position'].map_tax(
                self.partner_id.property_account_position, product_obj.taxes_id)
            pedido_linea_obj = self.env['sale.order.line']
            values_line = {
                'product_id': product_sale_id,
                'order_id': sale_order_id,   
                'type': 'make_to_order',    
                'name': name,
                'product_uom': product_obj.uom_id.id,
                'price_unit': subtotal_sale,
                'tax_id': [( 6, 0, tax_id)],
                'simulation_cost_line_ids': [( 6, 0, lines_ids)]}
            self.env['sale.order.line'].create(values_line)  

        ### CREO EL OBJETO SALE.ORDER.LINE PARA TASK LINES
        for data in task_datas:
            #Cojo los datos del array
            datos_array = task_datas[data]
            product_sale_id = datos_array['product_sale_id']
            subtotal_sale = datos_array['subtotal_sale'] 
            name = datos_array['name']
            lines_ids = datos_array['lines_ids']       
            context = {}
            lang = context.get('lang',False)
            context = {'lang': lang, 'partner_id': self.partner_id.id}
            product_id = self.env['product.product'].browse(product_sale_id)
            tax_id = self.env['account.fiscal.position'].map_tax(
                self.partner_id.property_account_position, product_obj.taxes_id)
            pedido_linea_obj = self.pool.get('sale.order.line')
            values_line = {
                'product_id': product_sale_id,
                'order_id': sale_order_id,      
                'type': 'make_to_order',  
                'name': name,
                'product_uom': product_obj.uom_id.id,
                'price_unit': subtotal_sale,
                'tax_id': [( 6, 0, tax_id)],
                'simulation_cost_line_ids': [( 6, 0, lines_ids)]
            }
            self.env['sale.order.line'].create(values_line)  
        ### CREO EL OBJETO SALE.ORDER.LINE PARA OTHERS LINES
        for data in others_datas:
            #Cojo los datos del array
            datos_array = others_datas[data]
            product_sale_id = datos_array['product_sale_id']
            subtotal_sale = datos_array['subtotal_sale'] 
            name = datos_array['name']
            lines_ids = datos_array['lines_ids']       
            context = {}
            lang = context.get('lang',False)
            context = {'lang': lang, 'partner_id': self.partner_id.id}         
            product_obj = self.env['product.product'].browse(product_sale_id)
            tax_id = self.env['account.fiscal.position'].map_tax(
                self.partner_id.property_account_position, product_obj.taxes_id)
            values_line = {
                'product_id': product_sale_id,
                'order_id': sale_order_id,            
                'name': name,
                'type': 'make_to_order',
                'product_uom': product_obj.uom_id.id,
                'price_unit': subtotal_sale,
                'tax_id': [( 6, 0, tax_id)],
                'simulation_cost_line_ids': [( 6, 0, lines_ids)]
            }
            self.env['sale.order.line'].create(values_line)  

        return True 
    ### BOTÓN HISTORIFICAR:
    @api.one
    def button_historificar(self):
        ### Leo el Objeto Coste
        ### valido que no esté historificado ya
        if self.historical_ok:
            raise exceptions.Warning(
                _('Historical Error'),
                _('Already Historical'))
        else:
            ### Le pongo la fecha del sistema
            fec_histo = fields.Date.context_today
            ### Modifico el Objeto con la fecha de historificación
            ### y con un booleano para indicar que el objeto esta historificado
            self.copy(self.id,{
                'historical_date': fec_histo,
                'historical_ok': True
            })          
        return True 
    ### BOTÓN CREAR NUEVA SIMULACION DE COSTES DESDE HISTORICO
    @api.one
    def button_create_newsimu_fromhisto(self):
        ### Leo el Objeto Simulación de coste
        ### Verifico que no exista una simulacion de coste que no este cancelada
        simulation_cost_ids = self.env['simulation.cost'].search([
            ('simulation_number','like',self.simulation_number[1:14]),
            ('historical_date','=',None),
            ('state','!=','canceled')])      
        if simulation_cost_ids:
            raise exceptions.Warning(
                _('Error Creating Simulation Cost'),
                _('There is a Simulation Cost'))
        ### Copio el objeto simulacion de coste.
        cost_simu_id = self.copy(self.id, {
            'historical_date': None,
            'historical_ok': False
        })     
        ### Al nuevo objeto simulación de coste le camio el serial     
        new_simulation_cost_obj = self.pool.get('simulation.cost')
        new_simulation_cost = new_simulation_cost_obj.browse(cost_simu_id)
        literal = new_simulation_cost.simulation_number + 'H'
        ### Actualizo el nuevo objeto de simulación de coste con el nuevo serial
        self.write([cost_simu_id],{
            'simulation_number': literal
        })  
        return True 
    ### BOTÓN COPIAR UNA SIMULACION DE COSTES
    @api.one
    def button_copy_cost_simulation(self):
        ### Creo la nueva simulacion de costes
        line_vals = {
            'name' : self.name,
            'overhead_costs': self.overhead_costs,
            'subtotal1_purchase': self.subtotal1_purchase,
            'subtotal1_sale': self.subtotal1_sale,
            'benefit1': self.benefit1,
            'subtotal2_purchase': self.subtotal2_purchase,
            'subtotal2_sale': self.subtotal2_sale,
            'benefit2': self.benefit2,
            'subtotal3_purchase': self.subtotal3_purchase,
            'subtotal3_sale': self.subtotal3_sale,
            'benefit3': self.benefit3,
            'subtotal4_purchase': self.subtotal4_purchase,
            'subtotal4_sale': self.subtotal4_sale,
            'benefit4': self.benefit4,
            'subtotal5_purchase': self.subtotal5_purchase,
            'subtotal5_sale': self.subtotal5_sale,
            'benefit5': self.benefit5,
            'subtotal1t_purchase': self.subtotal1t_purchase,
            'subtotal1t_sale': self.subtotal1t_sale,
            'benefit1t': self.benefit1t,
            'subtotal2t_purchase': self.subtotal2t_purchase,
            'subtotal2t_sale': self.subtotal2t_sale,
            'benefit2t': self.benefit2t,
            'subtotal3t_purchase': self.subtotal3t_purchase,
            'subtotal3t_sale': self.subtotal3t_sale,
            'benefit3t': self.benefit3t,
            'subtotal4t_purchase': self.subtotal4t_purchase,
            'subtotal4t_sale': self.subtotal4t_sale,
            'benefit4t': self.benefit4t,
            'subtotal5t_purchase': self.subtotal5t_purchase,
            'subtotal5t_sale': self.subtotal5t_sale,
            'benefit5t': self.benefit5t,
            'total_costs': self.total_costs,
            'total_sales': self.total_sales,
            'total_benefits': self.total_benefits,
            'total_amortizations': self.total_amortizations,
            'total_indirects': self.total_indirects,
            'total_amort_indirects': self.total_amort_indirects,
            'total_overhead_costs': self.total_overhead_costs,
            'total': self.total,
            'net_cost': self.net_cost,
            'net_cost_percentage': self.net_cost_percentage,
            'gross_margin': self.gross_margin,
            'gross_margin_percentage': self.gross_margin_percentage,
            'contribution_margin': self.contribution_margin,
            'contribution_margin_percentage': self.contribution_margin_percentage,
            'net_margin': self.net_margin,
            'net_margin_percentage': self.net_margin_percentage,
            'state': self.state
        }  
        simulation_cost_id = self.env['simulation.cost.line'].create(line_vals) 
        ### Copio las lineas compras
        for purchase_cost_line in self.purchase_cost_lines_ids:
            line_vals = {
                'simulation_cost_id' : simulation_cost_id,
                'product_id': purchase_cost_line.product_id.id,
                'name': purchase_cost_line.name,
                'description': purchase_cost_line.description,
                'supplier_id': purchase_cost_line.supplier_id.id,
                'purchase_price': purchase_cost_line.purchase_price,
                'uom_id': purchase_cost_line.uom_id.id,
                'amount': purchase_cost_line.amount,
                'product_sale_id': purchase_cost_line.product_sale_id.id,
                'sale_price': purchase_cost_line.sale_price,
                'estimated_margin': purchase_cost_line.estimated_margin,                   
                'estimated_date_purchase_completion': purchase_cost_line.estimated_date_purchase_completion,
                'amortization_rate': purchase_cost_line.amortization_rate,
                'amortization_cost': purchase_cost_line.amortization_cost,
                'indirect_cost_rate': purchase_cost_line.indirect_cost_rate,  
                'indirect_cost': purchase_cost_line.indirect_cost,                
                'type_cost': purchase_cost_line.type_cost,
                'type2': purchase_cost_line.type2,
                'type3': purchase_cost_line.type3,
                'template_id': purchase_cost_line.template_id.id
            }             
            self.env['simulation.cost.line'].create(line_vals)
        ### Copio las lineas investigacion
        for investment_cost_line in self.investment_cost_lines_ids:
            line_vals = {
                'simulation_cost_id' : simulation_cost_id,
                'product_id': investment_cost_line.product_id.id,
                'name': investment_cost_line.name,
                'description': investment_cost_line.description,
                'supplier_id': investment_cost_line.supplier_id.id,
                'purchase_price': investment_cost_line.purchase_price,
                'uom_id': investment_cost_line.uom_id.id,
                'amount': investment_cost_line.amount,
                'product_sale_id': investment_cost_line.product_sale_id.id,
                'sale_price': investment_cost_line.sale_price,
                'estimated_margin': investment_cost_line.estimated_margin,
                'estimated_date_purchase_completion': investment_cost_line.estimated_date_purchase_completion,
                'amortization_rate': investment_cost_line.amortization_rate,
                'amortization_cost': investment_cost_line.amortization_cost,
                'indirect_cost_rate': investment_cost_line.indirect_cost_rate,  
                'indirect_cost': investment_cost_line.indirect_cost,                
                'type_cost': investment_cost_line.type_cost,
                'type2': investment_cost_line.type2,
                'type3': investment_cost_line.type3,
                'template_id': investment_cost_line.template_id.id
            }
        ### Copio las lineas subcontratacion
        for subcontracting_cost_line in self.subcontracting_cost_lines_ids:
            line_vals = {
                'simulation_cost_id' : simulation_cost_id,
                'product_id': subcontracting_cost_line.product_id.id,
                'name': subcontracting_cost_line.name,
                'description': subcontracting_cost_line.description,
                'supplier_id': subcontracting_cost_line.supplier_id.id,
                'purchase_price': subcontracting_cost_line.purchase_price,
                'uom_id': subcontracting_cost_line.uom_id.id,
                'amount': subcontracting_cost_line.amount,
                'product_sale_id': subcontracting_cost_line.product_sale_id.id,
                'sale_price': subcontracting_cost_line.sale_price,
                'estimated_margin': subcontracting_cost_line.estimated_margin,
                'estimated_date_purchase_completion': subcontracting_cost_line.estimated_date_purchase_completion,
                'amortization_rate': subcontracting_cost_line.amortization_rate,
                'amortization_cost': subcontracting_cost_line.amortization_cost,
                'indirect_cost_rate': subcontracting_cost_line.indirect_cost_rate,  
                'indirect_cost': subcontracting_cost_line.indirect_cost,                   
                'type_cost': subcontracting_cost_line.type_cost,
                'type2': subcontracting_cost_line.type2,
                'type3': subcontracting_cost_line.type3,
                'template_id': subcontracting_cost_line.template_id.id} 
        ### Copio las lineas de tareas
        for task_cost_line in self.task_cost_lines_ids:
            line_vals = {
                'simulation_cost_id' : simulation_cost_id,
                'product_id': task_cost_line.product_id.id,
                'name': task_cost_line.name,
                'description': task_cost_line.description,
                'supplier_id': task_cost_line.supplier_id.id,
                'purchase_price': task_cost_line.purchase_price,
                'uom_id': task_cost_line.uom_id.id,
                'amount': task_cost_line.amount,
                'product_sale_id': task_cost_line.product_sale_id.id,
                'sale_price': task_cost_line.sale_price,
                'estimated_margin': task_cost_line.estimated_margin,
                'estimated_date_purchase_completion': task_cost_line.estimated_date_purchase_completion,
                'amortization_rate': task_cost_line.amortization_rate,
                'amortization_cost': task_cost_line.amortization_cost,
                'indirect_cost_rate': task_cost_line.indirect_cost_rate,  
                'indirect_cost': task_cost_line.indirect_cost,                   
                'type_cost': task_cost_line.type_cost,
                'type2': task_cost_line.type2,
                'type3': task_cost_line.type3,
                'template_id': task_cost_line.template_id.id
            } 
        ### Copio las lineas de otros
        for others_cost_line in self.others_cost_lines_ids:
            line_vals = {
                'simulation_cost_id' : simulation_cost_id,
                'product_id': others_cost_line.product_id.id,
                'name': others_cost_line.name,
                'description': others_cost_line.description,
                'supplier_id': others_cost_line.supplier_id.id,
                'purchase_price': others_cost_line.purchase_price,
                'uom_id': others_cost_line.uom_id.id,
                'amount': others_cost_line.amount,
                'product_sale_id': others_cost_line.product_sale_id.id,
                'sale_price': others_cost_line.sale_price,
                'estimated_margin': others_cost_line.estimated_margin,
                'estimated_date_purchase_completion': others_cost_line.estimated_date_purchase_completion,
                'amortization_rate': others_cost_line.amortization_rate,
                'amortization_cost': others_cost_line.amortization_cost,
                'indirect_cost_rate': others_cost_line.indirect_cost_rate,  
                'indirect_cost': others_cost_line.indirect_cost,                 
                'type_cost': others_cost_line.type_cost,
                'type2': others_cost_line.type2,
                'type3': others_cost_line.type3,
                'template_id': others_cost_line.template_id.id} 

        value = {
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'simulation.cost',
            'res_id': simulation_cost_id,
            'type': 'ir.actions.act_window',
            'nodestroy': True
        }
        return value

    ### FUNCIONES PARA EL TRATAMIENTO DEL WORKFLOW
    @api.one
    def action_draft(self):
        self.write({'state': 'draft'})
        return True
    
    @api.one
    def action_accepted(self):
        self.write({'state': 'accepted'})
        return True
    
    @api.one
    def action_canceled(self):
        self.write({'state': 'canceled'})
        return True
    ### Condicion para ejecutar el estado de workflow correspondiente
    @api.one
    def validar_historical(self):
        ### valido que no esté historificado ya
        if self.historical_ok:
            raise exceptions.Warning(
                _('Error'),
                _('This cost simulation have Historical'))
