# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
import logging
from openerp import models, api
_log = logging.getLogger(__name__)


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    @api.model
    def _create_service_task(self, procurement):
        """ Comprobar si la linea del pedido de venta tiene esta marcada
        para crear la tarea, de ser asi se crea, si no se pasa por alto """
        if procurement.sale_line_id.generate_task:
            task_id = super(ProcurementOrder, self)._create_service_task(
                procurement)
            task = self.env['project.task'].browse(task_id)
            project_id = self.env['project.project'].search([
                ('analytic_account_id', '=',
                 procurement.sale_line_id.order_id.project_id.id)])
            name = '%s-%s' % (
                procurement.sale_line_id.history_line_id.chapter_id.code,
                procurement.sale_line_id.history_line_id.chapter_id.name)
            # task.name = name
            # task.project_id = project_id

            task.write({
                'project_id': project_id.id or None,
                'name': name})
            return task_id
