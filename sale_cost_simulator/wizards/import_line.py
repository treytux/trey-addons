###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleCostImportLine(models.TransientModel):
    _name = 'sale.cost.import_line'
    _description = 'Wizard for import line'

    simulator_id = fields.Many2one(
        comodel_name='sale.cost.simulator',
        string='Simulator',
    )
    parent_id = fields.Many2one(
        comodel_name='sale.cost.line',
        string='Parent',
    )
    line_id = fields.Many2one(
        comodel_name='sale.cost.line',
        domain='[("child_ids", "!=", False)]',
        string='Line',
    )
    name = fields.Char(
        string='Rename to',
    )

    @api.onchange('line_id')
    def onchange_line_id(self):
        self.name = self.line_id.name

    @api.multi
    def button_accept(self):
        def set_simulator(line):
            line.simulator_id = self.simulator_id.id
            for line in line.child_ids:
                set_simulator(line)

        def copy_childs(line, parent_id):
            return line.copy(
                dict(simulator_id=self.simulator_id.id, parent_id=parent_id))

        parent = copy_childs(self.line_id, self.parent_id.id)
        parent.name = self.name
        set_simulator(parent)
