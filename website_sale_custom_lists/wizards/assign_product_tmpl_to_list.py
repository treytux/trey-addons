# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api, _, exceptions
import logging

_log = logging.getLogger(__name__)


class AssignProductTmplToList(models.TransientModel):
    _name = 'wiz.assign_product_tmpl_to_list'
    _description = 'Assign product templates to list.'

    name = fields.Char(
        string='Empty'
    )
    custom_list_id = fields.Many2one(
        comodel_name='custom.list',
        string='Custom list',
        required=True
    )
    empty_previously = fields.Boolean(
        string='Empty previously',
        help='If you select this field, the wizard will empty the list before '
        'adding new template products selected.'
    )

    @api.multi
    def button_accept(self):
        """ Anade las plantillas de producto seleccionadas a la lista elegida.
        """
        product_tmpls = self.env['product.template'].browse(
            self.env.context['active_ids'])

        if not product_tmpls.exists():
            raise exceptions.Warning(_(
                'You must select at least one product template.'))

        # Si ha marcado empty previously, eliminar las relaciones de todas las
        # plantillas de producto con la lista seleccionada y anadir las nuevas.
        if self.empty_previously:
            lines = self.env['custom.list.line'].search([
                ('custom_list_id', '=', self.custom_list_id.id)])

            for line in lines:
                line.unlink()

            for product_tmpl in product_tmpls:
                data = {
                    'custom_list_id': self.custom_list_id.id,
                    'product_tmpl_id': product_tmpl.id
                }
                self.env['custom.list.line'].create(data)
        else:
            # Anadir todas las plantillas de producto seleccionadas a la lista
            # elegida, evitando duplicados
            for product_tmpl in product_tmpls:
                # Comprobar que la plantilla no esta ya relacionada con la
                # lista
                lines = self.env['custom.list.line'].search([
                    ('custom_list_id', '=', self.custom_list_id.id),
                    ('product_tmpl_id', '=', product_tmpl.id)])
                # Si la plantilla no esta relacionada ya con la lista, se anade
                if not lines.exists():
                    data = {
                        'custom_list_id': self.custom_list_id.id,
                        'product_tmpl_id': product_tmpl.id
                    }
                    self.env['custom.list.line'].create(data)

        # Abrir vista
        res = self.env['ir.model.data'].get_object_reference(
            'website_sale_custom_lists',
            'wizard_wiz_assign_product_tmpl_to_list_finished')
        res_id = res and res[1] or False

        return {
            'name': _('Product templates assigned'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'wiz.assign_product_tmpl_to_list',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
        }
