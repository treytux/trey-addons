# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class EmailTemplate(models.Model):
    _inherit = 'email.template'

    @api.model
    def generate_recipients_batch(self, results, template_id, res_ids):
        picking_email_tmpl = self.env.ref(
            'stock_picking_send_by_mail.email_template_stock_picking')
        res = super(EmailTemplate, self).generate_recipients_batch(
            results, template_id, res_ids)
        if template_id != picking_email_tmpl.id:
            return res
        for res_id in res_ids:
            if len(res[res_id]['partner_ids']) == 0:
                return res
            partner_picking_id = (
                res[res_id]['partner_ids'] and res[res_id]['partner_ids'][0])
            partner_picking = self.env['res.partner'].browse(
                partner_picking_id)
            if not partner_picking.email:
                res[res_id]['partner_ids'] = (
                    partner_picking.parent_id and
                    partner_picking.parent_id.email and
                    [partner_picking.parent_id.id] or [partner_picking_id])
        return res
