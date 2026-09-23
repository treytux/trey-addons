###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class IrTranslatableMixin(models.AbstractModel):
    _name = 'ir.translatable.mixin'
    _description = 'Translatable Mixin'

    def action_open_translation_wizard(self):
        if len(self) > 1:
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
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ir.translation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_model_name': self._name,
                'default_record_id': self.id,
            },
        }
