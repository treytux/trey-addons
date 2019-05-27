###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime
from odoo import api, fields, models


class SalesStateReport(models.TransientModel):
    _name = 'sales.states.report_options'
    _description = 'Print options sales state'

    state_ids = fields.Many2many(
        comodel_name='res.country.state',
        default=None)
    agent_id = fields.Many2one(
        comodel_name='res.partner',
        domain=[('agent', '=', True)])
    date_from = fields.Date(
        string='From Date',
        default=datetime(year=datetime.now().year, month=1, day=1),
        required=True)
    date_to = fields.Date(
        string='To Date',
        default=datetime.now(),
        required=True)
    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        default=None)

    @api.multi
    def button_print(self, data):
        self.ensure_one()
        sale_state_rep = 'sale_report_states.report_sale_states_create'
        return self.env.ref(sale_state_rep).report_action(self, data={
            'state_ids': self.state_ids.ids,
            'agent_id': self.agent_id.id,
            'pricelist_id': self.pricelist_id.id,
            'date_from': self.date_from,
            'date_to': self.date_to})
