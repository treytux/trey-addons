# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import _, api, fields, models
from openerp.addons import decimal_precision as dp
from openerp.exceptions import ValidationError
from openerp.tools.float_utils import float_compare
import logging
_log = logging.getLogger(__name__)


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    bom_prod_price_total = fields.Float(
        string='Total Cost',
        compute='_compute_bom_prices',
        digits=dp.get_precision('Product Price'),
    )
    bom_lst_price_total = fields.Float(
        string='Total Price',
        compute='_compute_bom_prices',
        digits=dp.get_precision('Product Price'),
    )
    update_price_state = fields.Selection(
        string='Update Price State',
        selection=[
            ('updated', 'Updated'),
            ('cost', 'Cost'),
            ('sale', 'Sale'),
            ('both', 'Both'),
        ],
        required=True,
        default='updated',
    )
    is_manual_update = fields.Boolean(
        string='Manual Update',
    )
    is_formula = fields.Boolean(
        string='Formula',
    )
    type_formula = fields.Selection(
        string='Formula Type',
        selection=[
            ('none', 'None'),
            ('cost', 'Cost'),
            ('sale', 'Sale'),
            ('both', 'Both'),
        ],
        default='none',
    )
    standard_formula = fields.Text(
        string='Standard Formula',
        help='Use Python formula to calculate prices.\n Variable '
             'bom_lst_price for sales price.\n  bom_prod_price_total for '
             'cost price.',
    )
    list_formula = fields.Text(
        string='List Formula',
        help='Use Python formula to calculate prices.\n Variable '
             'bom_lst_price for sales price.\n  bom_prod_price_total for '
             'cost price.',
    )
    not_price_control = fields.Boolean(
        string='Not Price Control',
    )

    @api.constrains('standard_formula', 'list_formula')
    def check_formula(self):
        def check(bom_formula, type_formula):
            try:
                if not bom_formula:
                    return False
                formula = bom_formula.replace(
                    'bom_prod_price_total', '50.00')
                formula = formula.replace('bom_lst_price_total', '50.00')
                float(eval(formula))
            except ValueError:
                raise ValidationError(_(
                    'Formula %s Price Error: No Return Float Value') % (
                    type_formula))
            except Exception as e:
                raise ValidationError(_(
                    'Formula %s Price Error: %s' % (type_formula, e)))

        for bom in self:
            check(bom.standard_formula, 'Standard')
            check(bom.list_formula, 'List')

    @api.one
    @api.depends('bom_line_ids', 'standard_formula', 'list_formula')
    def _compute_bom_prices(self):
        def compute_formula(price_cost=0.00, price_list=0.00, formula=None):
            if not formula:
                return 0.00
            formula = formula.replace(
                'bom_prod_price_total', str(price_cost)).replace(
                'bom_lst_price_total', str(price_list))
            return float(eval(formula))

        cost_price = sum(li.bom_prod_price for li in self.bom_line_ids)
        list_price = sum(li.bom_lst_price for li in self.bom_line_ids)
        if self.type_formula == 'none':
            self.bom_prod_price_total = cost_price
            self.bom_lst_price_total = list_price
            return
        if self.type_formula == 'cost':
            self.bom_prod_price_total = compute_formula(
                cost_price, list_price, self.standard_formula)
            self.bom_lst_price_total = list_price
        if self.type_formula == 'sale':
            self.bom_lst_price_total = compute_formula(
                cost_price, list_price, self.list_formula)
            self.bom_prod_price_total = cost_price
        if self.type_formula == 'both':
            self.bom_prod_price_total = compute_formula(
                cost_price, list_price, self.standard_formula)
            self.bom_lst_price_total = compute_formula(
                cost_price, list_price, self.list_formula)
        return

    @api.multi
    def run_update_prices(self):
        for bom in self:
            if bom.is_manual_update or bom.not_price_control:
                return
            if bom.product_id:
                bom.product_id.lst_price = bom.bom_lst_price_total
                bom.product_id.standard_price = bom.bom_prod_price_total
            bom.product_tmpl_id.list_price = bom.bom_lst_price_total
            bom.product_tmpl_id.standard_price = bom.bom_prod_price_total
            bom.update_price_state = 'updated'

    @api.one
    def run_update_price_state(self):
        if self.not_price_control:
            return None
        is_list = bool(float_compare(
            self.product_id.lst_price if self.product_id else
            self.product_tmpl_id.lst_price, self.bom_lst_price_total,
            self.env.user.company_id.mrp_bom_standard_price_digit) != 0)
        is_cost = bool(float_compare(
            self.product_id.standard_price if self.product_id else
            self.product_tmpl_id.standard_price, self.bom_lst_price_total,
            self.env.user.company_id.mrp_bom_standard_price_digit) != 0)
        if is_cost and is_list:
            self.update_price_state = 'both'
        elif is_cost:
            self.update_price_state = 'cost'
        elif is_list:
            self.update_price_state = 'sale'

    @api.model
    def _run_bom_update_price(self):
        booms = self.env['mrp.bom'].search([
            ('update_price_state', '!=', 'updated'),
            ('is_manual_update', '=', False),
            ('not_price_control', '=', False),
        ])
        _log.info('Booms to Process Update Prices: %s' % len(booms))
        for bom in booms:
            bom.run_update_prices()

    @api.model
    def _run_bom_update_price_state(self):
        booms = self.env['mrp.bom'].search([
            ('is_manual_update', '=', False),
            ('not_price_control', '=', False),
        ])
        _log.info('Booms to Process if need Update Price: %s' % len(booms))
        for bom in booms:
            bom.run_update_price_state()
