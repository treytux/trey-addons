###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import io
import logging

from odoo import _, api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare

_log = logging.getLogger(__name__)
try:
    import pandas as pd
except (ImportError, IOError) as err:
    _log.debug(err)


class ImportProductionLotsWizard(models.TransientModel):
    _name = 'import.production.lots.wizard'
    _description = 'Import Lots/Serials'

    @api.model
    def default_get(self, fields):
        res = super(ImportProductionLotsWizard, self).default_get(fields)
        if self._context and self._context.get('active_id'):
            production = self.env['mrp.production'].browse(
                self._context['active_id'])
            main_product_moves = production.move_finished_ids.filtered(
                lambda x: x.product_id.id == production.product_id.id)
            todo_quantity = production.product_qty - sum(
                main_product_moves.mapped('quantity_done'))
            todo_quantity = todo_quantity if (todo_quantity > 0) else 0
            if 'production_id' in fields:
                res['production_id'] = production.id
            if 'todo_quantity' in fields:
                res['todo_quantity'] = todo_quantity
        return res

    production_id = fields.Many2one(
        comodel_name='mrp.production',
        string='Production Order',
    )
    todo_quantity = fields.Float(
        string='Quantity',
        digits=dp.get_precision('Product Unit of Measure'),
    )
    data_file = fields.Binary(
        string='File',
        required=True,
    )

    def _reopen_view(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.ids[0],
            'res_model': self._name,
            'target': 'new',
            'context': {},
        }

    def produce_move_lines(self):
        buf = io.BytesIO()
        buf.write(base64.b64decode(self.data_file))
        df = pd.read_excel(
            buf, engine='xlrd', na_values=['NULL'],
            converters={
                'default_code': str,
                'lot_material': str,
                'lot_final': str,
            }
        )
        lot_groups = {}
        if float_compare(len(df), self.todo_quantity, precision_digits=2) > 0:
            raise ValidationError(_(
                'You are trying to produce "%s" products and the production '
                'order only allows you to produce "%s".\n'
                'Please, delete lines from the file or modify the '
                'quantity to be produced from the production order.')
                % (len(df), self.todo_quantity))
        processed_products = set()
        for _index, row in df.iterrows():
            materials = self.production_id.bom_id.bom_line_ids.filtered(
                lambda x: x.product_id.default_code == row['default_code']
            ).mapped('product_id')
            if not materials:
                raise ValidationError(_(
                    'No product was found for default_code "%s".')
                    % row['default_code'])
            if len(materials) > 1:
                raise ValidationError(_(
                    'More than one product found for default_code "%s".')
                    % row['default_code'])
            lot = self.env['stock.lot'].search([
                ('name', '=', row['lot_material']),
                ('product_id', '=', materials.id),
            ])
            if not lot:
                raise ValidationError(_(
                    'No lot/serial was found for lot_material "%s".')
                    % row['lot_material'])
            processed_products.add(materials.id)
            lot_groups.setdefault(row['lot_final'], []).append(
                [row['default_code'], lot])
        production = self.production_id
        for raw_move in production.move_raw_ids:
            if raw_move.product_id.tracking != 'none' and \
                    raw_move.product_id.id not in processed_products:
                raise UserError(_(
                    'Please enter a lot or serial number for %s !')
                    % raw_move.product_id.display_name)
        production.move_raw_ids.move_line_ids.filtered(
            lambda ml: ml.qty_done == 0).unlink()
        cantidad_fabricar = len(lot_groups)
        production.qty_producing += cantidad_fabricar
        finished_move = production.move_finished_ids.filtered(
            lambda m: m.product_id == production.product_id)
        for lot_final_name, materials in lot_groups.items():
            lot_final = self.env['stock.lot'].search([
                ('name', '=', lot_final_name),
                ('product_id', '=', production.product_id.id),
                ('company_id', '=', production.company_id.id),
            ])
            if not lot_final:
                lot_final = self.env['stock.lot'].create({
                    'name': lot_final_name,
                    'product_id': production.product_id.id,
                    'company_id': production.company_id.id,
                })
            fin_line = finished_move.move_line_ids.filtered(
                lambda ml: ml.lot_id.id == lot_final.id)
            if fin_line:
                fin_line[0].write({
                    'qty_done': 1.0,
                })
            else:
                empty_fin = finished_move.move_line_ids.filtered(
                    lambda ml: not ml.lot_id)
                if empty_fin:
                    empty_fin[0].write({
                        'lot_id': lot_final.id, 'qty_done': 1.0,
                    })
                else:
                    self.env['stock.move.line'].create({
                        'move_id': finished_move.id,
                        'product_id': finished_move.product_id.id,
                        'product_uom_id': finished_move.product_uom.id,
                        'qty_done': 1.0,
                        'lot_id': lot_final.id,
                        'location_id': finished_move.location_id.id,
                        'location_dest_id': finished_move.location_dest_id.id,
                    })
            for default_code, lot_material in materials:
                raw_move = production.move_raw_ids.filtered(
                    lambda m: m.product_id.default_code == default_code)
                if raw_move:
                    raw_line = raw_move.move_line_ids.filtered(
                        lambda ml: ml.lot_id.id == lot_material.id)
                    if raw_line:
                        raw_line[0].write({'qty_done': 1.0})
                    else:
                        empty_raw = raw_move.move_line_ids.filtered(
                            lambda ml: not ml.lot_id)
                        if empty_raw:
                            empty_raw[0].write({
                                'lot_id': lot_material.id,
                                'qty_done': 1.0,
                            })
                        else:
                            self.env['stock.move.line'].create({
                                'move_id': raw_move.id,
                                'product_id': raw_move.product_id.id,
                                'product_uom_id': raw_move.product_uom.id,
                                'qty_done': 1.0,
                                'lot_id': lot_material.id,
                                'location_id': raw_move.location_id.id,
                                'location_dest_id': raw_move.location_dest_id.id,
                            })
        if production.product_qty > 0:
            factor = cantidad_fabricar / production.product_qty
            for raw_move in production.move_raw_ids:
                if raw_move.product_id.id not in processed_products:
                    raw_move.quantity_done += raw_move.product_uom_qty * factor
