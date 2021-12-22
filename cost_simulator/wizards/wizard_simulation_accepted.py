###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class WizardCostAccepted(models.TransientModel):
    _name = 'wizard.simulation.accepted'
    _description = 'Wizard Simulation Accepted'

    sale_type = fields.Selection(
        string='Sales Type',
        selection=[
            ('chapter', 'Per Chapter'),
            ('simulation', 'Per Simulation'),
        ],
        required=True,
        default='chapter',
    )

    @api.multi
    def button_ok(self):
        active_id = self.env.context.get('active_id', False)
        generate_task = False
        if active_id:
            cost_id = self.env['simulation.cost'].browse(active_id)
            # ******************************************************
            # Creo cuenta analitica y projecto para la simulacion
            # ******************************************************
            if not cost_id.company_id.project_template_id:
                raise ValidationError(
                    _('Please select Project Template for this company'))
            analytic_id = \
                cost_id.company_id.project_template_id.copy()
            analytic_id.partner_id = cost_id.partner_id.id
            analytic_id.name = '[%s]%s' % (
                cost_id.simulation_number, cost_id.name)
            analytic_id.type = 'contract'
            analytic_id.company_id = cost_id.company_id.id
            project_id = self.env['project.project'].search([(
                'analytic_account_id', '=', analytic_id.id)])[0]
            task_ids = []
            # ********************************************************
            #  Crear el pedido de venta por simulacion 1(pedido)
            # ********************************************************
            if self.sale_type == 'simulation':
                sale_id = self.env['sale.order'].create({
                    'partner_id': cost_id.partner_id.id,
                    'type_id': (
                        cost_id.company_id.project_sale_type_id.id or None),
                    'company_id': cost_id.company_id.id,
                    'client_order_ref': '%s-%s' % (
                        cost_id.simulation_number, cost_id.name)})

                for line in cost_id.simulation_line_ids:
                    if line.product_id.product_tmpl_id.auto_create_task:
                        name = '%s %s/%s' % (line.chapter_id.code,
                                             line.chapter_id.name,
                                             line.line_id.name)
                        planned_hours = self._convert_qty_company_hours(
                            line.product_id.product_tmpl_id, line)
                        task_ids.append((0, 0, {
                            'name': name,
                            'planned_hours': planned_hours,
                            'remaining_hours': planned_hours,
                            'partner_id': cost_id.partner_id.id,
                            'user_id': line.product_id.product_manager.id,
                            # 'project_id': analytic_id.id,
                            'company_id': cost_id.company_id.id,
                            'description': line.line_id.description,
                            'code': '/'}))
                    else:
                        name = line.line_id.name
                    self.env['sale.order.line'].create({
                        'order_id': sale_id.id,
                        'name': name,
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.quantity_sale,
                        'product_uom': line.line_id.uom_id.id,
                        'discount': line.discount_sale,
                        'price_unit': line.price_sale,
                        'partner_id': cost_id.partner_id.id,
                        'generate_task': generate_task,
                        'history_line_id': line.id,
                        'company_id': cost_id.company_id.id})
                sale_id.project_id = analytic_id.id
                cost_id.write({
                    'sale_order_ids': [(4, sale_id.id)],
                    'project_ids': [(4, analytic_id.id)]})
            else:
                # Chapter =  Pedido de venta por capitulo
                sale_ids = []
                for chapter_id in cost_id.chapter_ids:
                    line_ids = self.env['simulation.cost.history.line'].search(
                        [('chapter_id', '=', chapter_id.id),
                         ('history_id', '=', cost_id.simulation_id.id)])
                    sale_id = self.env['sale.order'].create({
                        'partner_id': cost_id.partner_id.id,
                        'company_id': cost_id.company_id.id,
                        'type_id':
                            cost_id.company_id.project_sale_type_id.id or None,
                        'client_order_ref': '%s-%s' % (
                            cost_id.simulation_number, cost_id.name),
                    })
                    for line in line_ids:
                        if line.product_id.product_tmpl_id.auto_create_task:
                            name = '%s %s/%s' % (line.chapter_id.code,
                                                 line.chapter_id.name,
                                                 line.line_id.name)
                            planned_hours = self._convert_qty_company_hours(
                                line.product_id.product_tmpl_id, line)
                            task_ids.append((0, 0, {
                                'name': name,
                                'planned_hours': planned_hours,
                                'remaining_hours': planned_hours,
                                'partner_id': cost_id.partner_id.id,
                                'user_id': line.product_id.product_manager.id,
                                'project_id': analytic_id.id,
                                'company_id': cost_id.company_id.id,
                                'description': line.line_id.description,
                                'code': '/'}))
                        else:
                            name = line.line_id.name
                            self.env['sale.order.line'].create({
                                'order_id': sale_id.id,
                                'name': name,
                                'product_id': line.product_id.id,
                                'product_uom_qty': line.quantity_sale,
                                'product_uom': line.line_id.uom_id.id,
                                'discount': line.discount_sale,
                                'price_unit': line.price_sale,
                                'partner_id': cost_id.partner_id.id,
                                'generate_task': generate_task,
                                'history_line_id': line.id})
                    sale_ids.append(sale_id.id)
                    sale_id.project_id = analytic_id.id
                cost_id.write({
                    'sale_order_ids': [(6, 0, sale_ids)],
                    'project_ids': [(6, 0, analytic_id._ids)]})
            # Crear las tareas asociadas al proyecto
            project_id.write({'tasks': task_ids})
            cost_id.state = 'accepted'
            cost_id.project_type = 'open'
            cost_id.sale_type = self.sale_type

    def _convert_qty_company_hours(self, product, line):
        company_time_uom_id = self.env.user.company_id.project_time_mode_id
        if product.uom_id.id != company_time_uom_id.id and \
           product.uom_id.category_id.id == company_time_uom_id.category_id.id:
            planned_hours = self.env['product.uom']._compute_qty(
                product.uom_id.id, line.quantity_sale,
                company_time_uom_id.id)
        else:
            planned_hours = line.quantity_sale
        return planned_hours
