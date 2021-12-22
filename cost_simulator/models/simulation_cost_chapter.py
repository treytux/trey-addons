###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SimulationCostChapter(models.Model):
    _name = 'simulation.cost.chapter'
    _description = 'Simulation Cost Chapter'
    _order = 'sequence, code'

    cost_id = fields.Many2one(
        comodel_name='simulation.cost',
        string='Cost',
        required=True,
        index=True,
        ondelete='cascade',
    )
    chapter_tmpl_id = fields.Many2one(
        comodel_name='simulation.cost.chapter.template',
        string='Chapter template',
        readonly=True,
        required=True,
    )
    sequence = fields.Integer(
        string='Sequence',
    )
    code = fields.Char(
        string='Reference',
    )
    name = fields.Char(
        string='Name',
        required=True,
    )
    description = fields.Text(
        string='Description',
    )
    subtotal_cost = fields.Float(
        string='Subtotal Purchase',
        readonly=True,
    )
    subtotal_sale = fields.Float(
        string='Subtotal Sale',
        readonly=True,
    )
    subtotal_benefits = fields.Float(
        string='Subtotal Benefits',
        readonly=True,
    )

    @api.multi
    def name_get(self):
        res = []
        for r in self:
            tmp = r.chapter_tmpl_id
            name = tmp and '%s/' % tmp.name or ''
            res.append((r.id, '%s%s' % (name, r.name)))
        return res

    @api.multi
    def compute(self):
        for cost in self:
            for line in cost.cost_id.line_ids:
                if line.chapter_tmpl_id not in cost.chapter_tmpl_id.child_ids:
                    continue
                cost.subtotal_cost += line.subtotal_cost
