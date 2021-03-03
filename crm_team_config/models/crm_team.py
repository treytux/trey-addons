##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from odoo import api, fields, models


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    warehouse_ids = fields.Many2many(
        comodel_name='stock.warehouse',
        relation='crm_team2warehouse_rel',
        column1='crm_team_id',
        column2='warehouse_id',
        string='Warehouses',
    )
    location_ids = fields.Many2many(
        comodel_name='stock.location',
        relation='crm_team2location_rel',
        column1='crm_team_id',
        column2='location_id',
        string='Locations',
        readonly=True,
    )
    payment_journal_ids = fields.Many2many(
        comodel_name='account.journal',
        relation='crm_team2payment_journal_rel',
        column1='crm_team_id',
        column2='payment_journal_id',
        domain=[('type', 'in', ('bank', 'cash'))],
        string='Payment journals',
    )
    invoice_journal_ids = fields.Many2many(
        comodel_name='account.journal',
        relation='crm_team2invoice_journal_rel',
        column1='crm_team_id',
        column2='invoice_journal_id',
        string='Invoice journals',
    )

    @api.model
    def create(self, vals):
        res = super().create(vals)
        res._compute_locations()
        return res

    def write(self, vals):
        res = super().write(vals)
        if 'location_ids' not in vals:
            self._compute_locations()
        return res

    def _compute_locations(self):
        def _get_locations_by_warehouse(warehouses):
            locations = self.env['stock.location']
            for warehouse in warehouses:
                locations |= locations.search([
                    ('id', 'child_of', warehouse.view_location_id.id)])
            return locations

        for team in self:
            locations = _get_locations_by_warehouse(team.warehouse_ids)
            team.location_ids = [(6, 0, locations.ids)]
