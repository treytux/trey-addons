###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    unit_id = fields.Many2one(
        comodel_name='product.business.unit',
        string='Business unit',
    )
    area_id = fields.Many2one(
        comodel_name='product.business.area',
        string='Area',
    )

    def _select(self):
        return '%s, sub.unit_id, sub.area_id' % (super()._select())

    def _sub_select(self):
        return '%s, pt.unit_id as unit_id, pt.area_id as area_id' % (
            super()._sub_select())

    def _group_by(self):
        return '%s, pt.unit_id, pt.area_id' % super()._group_by()
