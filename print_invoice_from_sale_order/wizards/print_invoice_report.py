# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api, exceptions, _


class PrintInvoiceReport(models.TransientModel):
    _name = 'wiz.print_invoice_report'

    # Obtiene los informes de factura
    def _get_default_report(self):
        report_ids = self.env['ir.actions.report.xml'].search(
            [('model', '=', 'account.invoice')])

        if report_ids:
            return report_ids[0]
        else:
            raise exceptions.Warning(
                _('Atencion'),
                _('No hay ningun informe disponible para la factura.')
            )

    report_id = fields.Many2one(
        comodel_name='ir.actions.report.xml',
        string='Report',
        domain=[('model', '=', 'account.invoice')],
        default=_get_default_report,
        required=True
    )

    @api.multi
    def button_print_invoice(self):

        # Buscar el id del pedido
        order_ids = self.env.context['active_ids']
        orders = self.env['sale.order'].browse(order_ids)

        # Buscar facturas asociadas a los pedidos
        invoice_ids = [
            i.id for o in orders for i in o.invoice_ids if i.state != 'cancel']

        # Si no hay factura, mostrar msg
        if not invoice_ids:
            raise exceptions.Warning(_('MENSAJE'))

        # Si hay factura/s, lanzar el report con los ids de la/s factura/s
        datas = {'ids': invoice_ids}

        # Lanzar informe
        return {
            'type': 'ir.actions.report.xml',
            'report_name': self.report_id.report_name,
            'datas': datas,
        }
