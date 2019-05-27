# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models, fields


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    @api.multi
    @api.depends('product_id.product_tmpl_id.state')
    def _compute_name_product_end_or_obsolete(self):
        for procurement in self:
            procurement.product_end_or_obsolete = (
                procurement.product_id.product_tmpl_id.state in (
                    'end', 'obsolete') and True or False)

    product_end_or_obsolete = fields.Boolean(
        compute='_compute_name_product_end_or_obsolete',
        store=True,
        string="Product in 'Obsolete' or 'End of lifecycle state'",
        help="The procurement orders that have this field marked will never "
             "be executed because the associated product has an 'Obsolete' or "
             "'End of lifecycle state' state assigned.")

    @api.multi
    def run(self, autocommit=False):
        if not self:
            return super(ProcurementOrder, self).run(autocommit=autocommit)
        new_proc_ids = []
        for proc in self:
            if proc.product_id.state not in ('end', 'obsolete'):
                new_proc_ids.append(proc.id)
        if not new_proc_ids:
            empty_proc = self.env['procurement.order']
            return super(ProcurementOrder, empty_proc).run(
                autocommit=autocommit)
        new_procs = self.browse(new_proc_ids)
        return super(ProcurementOrder, new_procs).run(autocommit=autocommit)
