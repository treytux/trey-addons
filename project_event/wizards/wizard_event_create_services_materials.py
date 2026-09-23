###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class WizardEventCreateServicesMaterials(models.TransientModel):
    _name = 'wizard.event.create.services.materials'
    _description = 'Wizard to generate event services and materials'

    line_ids = fields.One2many(
        comodel_name='wizard.event.create.services.materials.line',
        inverse_name='wizard_id',
        string='Lines',
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if 'line_ids' not in res:
            res['line_ids'] = []
        events = self.env['event.event'].browse(
            self.env.context.get('active_ids', []))
        lines = self.env['wizard.event.create.services.materials.line']
        for event in events:
            product_ids = []
            for service_line in event.service_line_ids:
                if (service_line.task_id or not service_line.product_id
                        or service_line.product_id.id in product_ids):
                    continue
                line_data = {
                    'wizard_id': self.id,
                    'product_id': service_line.product_id.id,
                }
                lines |= lines.create(line_data)
        res.update({
            'line_ids': [(6, 0, lines.ids)],
        })
        return res

    def button_confirm(self):
        self.ensure_one()
        active_ids = self.env.context.get('active_ids', False)
        if not active_ids:
            raise ValidationError(_('You must select at least one event'))
        event_obj = self.env['event.event']
        products_to_generate = self.line_ids.filtered(
            lambda ln: ln.generate).mapped('product_id.id')
        if not products_to_generate:
            raise ValidationError(_('No lines to generate'))
        for event in event_obj.browse(active_ids):
            event.create_services_and_material(products_to_generate)
        return True


class WizardEventCreateServicesMaterialsLine(models.TransientModel):
    _name = 'wizard.event.create.services.materials.line'
    _description = 'Wizard lines to generate event services and materials'

    wizard_id = fields.Many2one(
        comodel_name='wizard.event.create.services.materials',
        string='Wizard',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        required=True,
    )
    generate = fields.Boolean(
        default=True,
    )
