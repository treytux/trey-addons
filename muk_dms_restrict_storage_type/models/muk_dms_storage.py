###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class MukDmsStorage(models.Model):
    _inherit = 'muk_dms.storage'

    save_type = fields.Selection(
        selection=[
            ('file', 'Filestore'),
        ],
    )
