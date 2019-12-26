###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields, api, _


class RecalculateCostCategoryPrice(models.TransientModel):
    _name = 'recalculate.cost.category.price'
    _description = 'Recalculate Cost Category Price'

    category_id = fields.Many2one(
        comodel_name='product.cost.category',
        string='Category',
    )
    log = fields.Text(
        string='Log',
    )
    state = fields.Selection(
        string='State',
        selection=[('step1', 'Step1'),
                   ('done', 'Done')],
        required=True,
        default='step1')

    @api.multi
    def _reopen_view(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.ids[0],
            'res_model': self._name,
            'target': 'new',
            'context': {}}

    @api.multi
    def recalculate_cost_category_price(self):
        active_ids = self.env.context['active_ids']
        templates = self.env['product.template'].browse(active_ids)
        if not templates:
            return
        ctx = self.env.context.copy()
        ctx['selection_category'] = self.category_id or None
        ctx['update_from_wizard'] = True
        for template in templates:
            template.with_context(ctx)._compute_template_cost_category_price()
        log = _('I have Update %s Templates and their variants' % len(
            active_ids))
        self.write({'state': 'done', 'log': log})
        self._reopen_view()
