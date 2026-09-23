###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = ['product.template', 'ir.translatable.mixin']

    def action_open_bulk_translation_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ir.translation.bulk.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_model_name': self._name,
                'active_ids': self.ids,
                'active_model': self._name,
            },
        }
