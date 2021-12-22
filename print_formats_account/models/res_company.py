###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    invoice_report_group_by = fields.Selection(
        selection=[
            ('order', 'Order'),
            ('picking', 'Picking'),
        ],
        string='Invoice Report Group By',
    )

    invoice_report_hide_qty_column = fields.Boolean(
        string='Hide report quantity column',
        help='When this setting is set, hides quantity column in report '
             'invoice when every line quantity is equal to 1',
    )
