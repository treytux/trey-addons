# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api, _, exceptions
from dateutil.relativedelta import relativedelta
from datetime import datetime

import logging

_log = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    contract_type_id = fields.Many2one(
        comodel_name='contract.type',
        string='Contract Type')

    @api.multi
    def onchange_partner_id(self, partner_id):
        """Al asignar el cliente, se asigna el tipo de contrato que tenga."""
        res = super(SaleOrder, self).onchange_partner_id(partner_id)
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            res['value']['contract_type_id'] = partner.contract_type_id and \
                partner.contract_type_id.id or None
        else:
            res['value']['contract_type_id'] = False
        return res

    @api.onchange('contract_type_id')
    def onchange_contract_type_id(self):
        """Al asignar el tipo de contrato, se crean las lineas de pedido con
        los productos definidos en dicho tipo de contrato."""

        lines = []
        if self.contract_type_id:
            # Si tiene tipo de contrato asignado, crear lineas de pedido
            for product_line in self.contract_type_id.product_ids:
                pricelist = self.partner_id.property_product_pricelist
                if not pricelist:
                    raise exceptions.Warning(
                        _('This customer has not defined sales pricelist, you '
                          'must assign one.'))
                # Leer el precio de la linea de productos y, si tiene producto
                # asociado, se le aplica la tarifa del pedido o la del cliente
                if product_line.product_id:
                    # Calculamos el precio de una unidad porque luego pasamos
                    # la cantidad a la linea de pedido
                    price_unit = pricelist.price_get(
                        product_line.product_id.id,
                        product_line.qty)[pricelist.id]
                    tax_ids = product_line.product_id.product_tmpl_id.taxes_id
                else:
                    price_unit = product_line.price_unit
                    tax_ids = product_line.tax_ids
                # Posicion fiscal
                fiscal_position =\
                    self.partner_id.property_account_position or None
                # A los impuestos del producto se le aplica la posicion fiscal
                # (si el cliente la tiene asignada)
                tax = fiscal_position and fiscal_position.map_tax(tax_ids) or\
                    tax_ids
                line_data = {
                    'product_id': product_line.product_id and
                    product_line.product_id.id or None,
                    'product_uom_qty': product_line.qty,
                    'product_uom':
                        product_line.product_id and
                        product_line.product_id.product_tmpl_id and
                        product_line.product_id.product_tmpl_id.uom_id and
                        product_line.product_id.product_tmpl_id.uom_id.id or
                        None,
                    'price_unit': price_unit,
                    'name': product_line.name,
                    'tax_id': [(6, 0, [t.id for t in tax])],
                    'state': 'draft',
                    'product_contract_type_ids': [(6, 0, [product_line.id])],
                }
                lines.append((0, 0, line_data))
        if lines:
            self.order_line = lines

    def print_quotation(self, cr, uid, ids, context=None):
        ''' Heredar funcion lanzada por el boton imprimir para que, dependiento
        de ciertas condiciones, imprima una cosa u otra:
        - Si no tiene asignado tipo de contrato, imprimir el pedido de venta
          (como antes)
        - En otro caso
             Imprimir pedido + contrato (definidos en el tipo de contrato)
        '''

        if ids:
            order = self.pool.get('sale.order').browse(
                cr, uid, ids[0], context=context)

            if not order.contract_type_id:
                return super(SaleOrder, self).print_quotation(
                    cr, uid, ids, context)

            else:
                # assert len(ids) == 1,
                # 'This option should only be used for a single id at a time'

                return self.pool['report'].get_action(
                    cr, uid, ids,
                    'print_contract_report.sale_contract',
                    context=context
                )

    @api.one
    def action_button_confirm(self):
        '''Heredar funcion para que al confirmar el pedido de venta, se
        compruebe si tiene tipo de contrato asignado y, si es asi, se cree un
        contrato y se relacione con el pedido. Ademas, se asignara a las tareas
        generadas por los productos de las lineas que tienen marcada la opcion
        'Crear tarea automaticamente' el proyecto que genera el contrato de
        forma automatica.'''

        res = super(SaleOrder, self).action_button_confirm()

        if not self.contract_type_id.exists():
            return res

        # Crear el contrato
        data = {
            'name': 'Contrato %s (%s)' % (
                self.contract_type_id.name, self.name),
            'partner_id': self.partner_id.id,
            'contract_type_id': self.contract_type_id.id,
            'type': 'contract',
            'use_tasks': True,
            'date_start': fields.Date.context_today(self),
            # Todos los contratos son anuales, le asignamos fecha fin
            'date': (datetime.today() +
                     relativedelta(years=1, days=-1)).date(),
        }
        contract = self.env['account.analytic.account'].create(data)
        _log.info('Creado contrato %s' % contract)

        # Asignar el contrato al pedido
        order = self.env['sale.order'].browse(self.id)
        order.write({'project_id': contract.id})

        # Buscar el proyecto que ha creado el contrato para asignarlo a la
        # tarea
        projects = self.env['project.project'].search([
            ('analytic_account_id', '=', contract.id)])

        # Buscar las tareas que ha generado el pedido y asignarles el proyecto
        line_ids = [l.id for l in order.order_line]

        tasks = self.env['project.task'].search([
            ('sale_line_id', 'in', line_ids)])
        for task in tasks:
            if task[0].exists() and projects[0].exists():
                task[0].write({'project_id': projects[0].id})

        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_contract_type_ids = fields.Many2many(
        comodel_name='product.contract.type',
        relation='sale_order_line_prod_contract_type_rel',
        column1='order_line_id',
        column2='product_contract_type_id')
