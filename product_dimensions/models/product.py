# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.


from openerp import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.onchange('length', 'high', 'width', 'dimensional_uom')
    def onchange_calculate_volume(self):
        if not self.length or not self.high \
           or not self.width or not self.dimensional_uom:
            self.volume = 0
        else:
            if self.dimensional_uom.uom_type == 'bigger':
                factor = self.dimensional_uom.factor
            elif self.dimensional_uom.uom_type == 'smaller':
                factor = 1 / self.dimensional_uom.factor
            else:
                factor = 1
            length_m = self.length * factor
            high_m = self.high * factor
            width_m = self.width * factor
            self.volume = length_m * high_m * width_m

    length = fields.Float(string='Length')
    high = fields.Float('High')
    width = fields.Float('Width')
    dimensional_uom = fields.Many2one(
        comodel_name='product.uom',
        string='UdM dimensional',
        help='Unidad de Medida Dimensional para Largo, Alto y Ancho')
