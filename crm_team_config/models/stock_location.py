##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from odoo import api, models


class StockLocation(models.Model):
    _inherit = 'stock.location'

    def recompute_crm_team_locations(self):
        self.ensure_one()
        wh = self.get_warehouse()
        teams = self.env['crm.team'].search([])
        teams.write({'location_ids': [(3, self.id)]})
        teams = self.env['crm.team'].search([('warehouse_ids', 'in', wh.ids)])
        teams.write({'location_ids': [(4, self.id)]})

    @api.model
    def create(self, vals):
        res = super().create(vals)
        res.recompute_crm_team_locations()
        return res

    @api.multi
    def write(self, vals):
        res = super().write(vals)
        for location in self:
            location.recompute_crm_team_locations()
        return res
