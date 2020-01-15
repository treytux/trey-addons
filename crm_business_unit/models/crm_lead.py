###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    business_unit_ids = fields.Many2many(
        comodel_name='product.business.unit',
        relation='productbusinessunit2crm',
        column1='lead_id',
        column2='unit_id',
    )
