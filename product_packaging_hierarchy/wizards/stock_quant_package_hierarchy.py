###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockQuantPackageHierarchy(models.TransientModel):
    _name = 'stock.quant.package.hierarchy'
    _description = 'Stock package hierarchy'

    name = fields.Char(
        string='Package name',
        help='If left empty the name will be filled with the default value.',
    )
    parent_package_id = fields.Many2one(
        comodel_name='stock.quant.package',
        string='Parent package',
        help='Package that will contain the current package (for example a '
             'pallet or package that contains other packages).',
    )

    def update_package(self, package):
        vals = {
            'parent_id': self.parent_package_id.id,
        }
        if self.name:
            vals.update({
                'name': self.name,
            })
        package.write(vals)

    def action_confirm(self):
        pickings = self.env['stock.picking'].browse(
            self.env.context['active_ids'])
        for picking in pickings:
            res = picking.put_in_pack()
            if isinstance(res, dict):
                package_id = (
                    res.get('context')
                    and res['context'].get('default_stock_quant_package_id'))
                package = self.env['stock.quant.package'].browse(package_id)
            else:
                package = res
            if package:
                self.update_package(package)
        return True
