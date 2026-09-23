###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    maintenance_product_tmpl_id = fields.Many2one(
        related='company_id.maintenance_product_tmpl_id',
        comodel_name='product.template',
        string='Maintenance product template',
        readonly=False,
    )
