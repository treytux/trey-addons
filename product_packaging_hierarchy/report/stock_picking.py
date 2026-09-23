###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ReportPrintProductPackage(models.AbstractModel):
    _name = 'report.product_packaging_hierarchy.report_product_package'
    _description = 'Product Package Hierarchy Report'

    def build_package_tree(self, packages):
        package_tree = []
        package_id_list = []

        def _get_recursive_package(package):
            if not package.parent_id:
                return package.id
            return _get_recursive_package(package.parent_id)

        def add_package_to_tree(listed_package):
            package_data = {
                'object': listed_package,
                'subpackages': []
            }
            subpackages = package_list.filtered(
                lambda p: p.parent_id == listed_package)
            for subpackage in subpackages:
                subpackage_data = add_package_to_tree(subpackage)
                package_data['subpackages'].append(subpackage_data)
            return package_data

        for package in packages.sorted(key=lambda p: p.name):
            if package.id not in package_id_list:
                package_id_list.append(package.id)
            package_id = _get_recursive_package(package)
            if package_id not in package_id_list:
                package_id_list.append(package_id)
        package_list = self.env['stock.quant.package'].browse(package_id_list)
        top_level_packages = package_list.filtered(lambda p: not p.parent_id)
        for listed_package in top_level_packages:
            package_data = add_package_to_tree(listed_package)
            package_tree.append(package_data)
        return package_tree

    @api.multi
    def _get_report_values(self, docids, data=None):
        docs = self.env['stock.picking'].browse(docids)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'stock.picking',
            'docs': docs,
            'package_tree': self.build_package_tree,
        }
