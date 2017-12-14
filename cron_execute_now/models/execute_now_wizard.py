# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
#
from openerp import models, fields, api


class ExecuteCronNow(models.TransientModel):
    _name = 'execute_cron_now.wizard'

    name = fields.Char(
        string='Empty'
    )

    @api.multi
    def action_accept(self):
        if 'active_ids' in self._context:
            cron = self.env['ir.cron'].browse(self._context['active_ids'])
            self.env['ir.cron']._callback(cron.model, cron.function,
                                          cron.args, cron.id)
        return {}
