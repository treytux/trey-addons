###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64

from odoo import _, api, exceptions, fields, models


class ExportBmcatWizard(models.TransientModel):
    _name = 'export.bmcat.wizard'
    _description = 'BMEcat export wizard'

    catalog_id = fields.Many2one(
        comodel_name='product.catalog',
        string='Catalog',
        required=True,
        domain=[
            ('bmcat_token', '!=', False),
        ],
    )
    product_count = fields.Integer(
        string='Product count',
        compute='_compute_product_count',
    )
    state = fields.Selection(
        selection=[
            ('select', 'Select'),
            ('done', 'Done'),
        ],
        default='select',
        readonly=True,
    )
    bmcat_file = fields.Binary(
        string='BMEcat file',
        readonly=True,
    )
    bmcat_filename = fields.Char(
        string='Filename',
        readonly=True,
    )

    @api.depends('catalog_id')
    def _compute_product_count(self):
        for rec in self:
            if rec.catalog_id:
                rec.product_count = self.env['product.template'].search_count([
                    ('catalog_ids', 'in', rec.catalog_id.id),
                ])
            else:
                rec.product_count = 0

    def action_export(self):
        self.ensure_one()
        if not self.catalog_id:
            raise exceptions.UserError(_('Please select a catalog.'))
        products = self.env['product.template'].search([
            ('catalog_ids', 'in', self.catalog_id.id),
        ])
        if not products:
            raise exceptions.UserError(
                _('No products found in the selected catalog.'))
        xml_content = self.catalog_id._bmcat_generate_xml(products)
        self.catalog_id._bmcat_store_file(xml_content)

        self.write({
            'state': 'done',
            'bmcat_file': (
                base64.b64encode(xml_content) if xml_content else False),
            'bmcat_filename': self.catalog_id.bmcat_filename or 'catalog.xml',
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'export.bmcat.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
