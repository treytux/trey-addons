###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class GoodsFreeMassCreate(models.TransientModel):
    _name = 'goods_free.mass.create'
    _description = 'Wizard to create goods free'

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True,
    )
    percent = fields.Float(
        string='Goods free (%)',
        required=True,
    )
    season_id = fields.Many2one(
        comodel_name='product.season',
        string='Season',
    )
    categ_ids = fields.Many2many(
        comodel_name='product.public.category',
        relation='goods_free2categ_id_rel',
        column1='good_free_mass_id',
        column2='categ_id',
        string='Categories',
    )
    step = fields.Integer(
        string='Wizard steps',
        default=0,
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

    def update_goods_free(self, partner, products, percent):
        goods_free = self.env['res.partner.goods_free'].search([
            ('partner_id', '=', partner.id),
            ('product_id', 'in', products.ids),
        ])
        goods_free.write({
            'percent': percent,
        })
        return goods_free.mapped('product_id')

    def create_goods_free_wizard(self, partner, products, percent):
        products_update = self.update_goods_free(partner, products, percent)
        products = products - products_update
        goods_free_obj = self.env['res.partner.goods_free']
        for product in products:
            goods_free_obj.create({
                'partner_id': partner.id,
                'product_id': product.id,
                'percent': percent,
            })

    def button_create_goods_free_all_products(self):
        products = self.env['product.product'].search([])
        self.create_goods_free_wizard(self.partner_id, products, self.percent)
        self.step = 1
        return self._reopen_view()

    def button_create_goods_free(self):
        self.ensure_one()
        if not self.categ_ids and not self.season_id:
            self.step = 2
            return self._reopen_view()
        domain = []
        if self.season_id:
            domain.append(('season_id', '=', self.season_id.id))
        if self.categ_ids:
            domain.append(('public_categ_ids', 'in', self.categ_ids.ids))
        products = self.env['product.product'].search(domain)
        self.create_goods_free_wizard(self.partner_id, products, self.percent)
        self.step = 1
        return self._reopen_view()
