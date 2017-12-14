# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api
import logging
_log = logging.getLogger(__name__)


class SimulationCostChapter(models.Model):
    _name = 'simulation.cost.chapter'
    _description = 'Simulation Cost Chapter'
    _order = 'sequence, code'

    cost_id = fields.Many2one(
        comodel_name='simulation.cost',
        string='Cost',
        required=True,
        index=True,
        ondelete='cascade')
    chapter_tmpl_id = fields.Many2one(
        comodel_name='simulation.cost.chapter.template',
        string='Chapter template',
        readonly=True,
        required=True)
    sequence = fields.Integer(
        string='Sequence',
        required=False)
    code = fields.Char(
        string='Reference',
        store=True)
    name = fields.Char(
        string='Name',
        required=True)
    description = fields.Text(
        string='Description')
    subtotal_cost = fields.Float(
        string='Subtotal Purchase',
        readonly=True)
    subtotal_sale = fields.Float(
        string='Subtotal Sale',
        readonly=True)
    subtotal_benefits = fields.Float(
        string='Subtotal Benefits',
        readonly=True)

    @api.multi
    def name_get(self):
        res = []
        for r in self:
            tmp = r.chapter_tmpl_id
            name = tmp and '%s/' % tmp.name or ''
            res.append((r.id, '%s%s' % (name, r.name)))
        return res

    @api.one
    def compute(self):
        for line in self.cost_id.line_ids:
            if line.chapter_tmpl_id not in self.chapter_tmpl_id.child_ids:
                continue
            self.subtotal_cost += line.subtotal_cost


class SimulationCost(models.Model):
    _inherit = 'simulation.cost'

    chapter_ids = fields.One2many(
        comodel_name='simulation.cost.chapter',
        inverse_name='cost_id',
        string='Simulation Cost',
        copy=True)
    total_costs = fields.Float(
        string='Total Costs',
        readonly=True,
        compute='compute_chapter')
    total_sales = fields.Float(
        string='Total Sales',
        readonly=True,
        compute='compute_chapter')
    total_benefits = fields.Float(
        string='Total Benefits',
        readonly=True,
        compute='compute_chapter')

    @api.one
    @api.depends('line_ids', 'simulation_line_ids')
    def update_chapters(self):
        tmpls_now = list(set([c.chapter_tmpl_id.id for c in self.chapter_ids]))

        def _create_chapter(tmpl):
            if tmpl.id not in tmpls_now:
                tmpls_now.append(tmpl.id)
                self.chapter_ids.create({
                    'cost_id': self.id,
                    'chapter_tmpl_id': tmpl.id,
                    'name': tmpl.name,
                    'description': tmpl.description,
                })

        def _create_chapter_recursive(tmpl):
            if not tmpl.parent_id:
                _create_chapter(tmpl)
                return False
            _create_chapter_recursive(tmpl.parent_id)
            _create_chapter(tmpl)

        for line in self.line_ids:
            _create_chapter_recursive(line.chapter_tmpl_id)

        self.compute_chapter()

    @api.one
    def compute_chapter(self):
        self.ensure_one()
        self.total_sales = 0
        self.total_costs = 0
        self.total_benefits = 0

        for chapter in self.chapter_ids:
            chapter.subtotal_cost = 0
            chapter.subtotal_sale = 0
            chapter.subtotal_benefits = 0

        def sum_chapter(tmpl_id, cost=0, sale=0):
            for chapter in self.chapter_ids:
                if chapter.chapter_tmpl_id.id == tmpl_id:
                    chapter.subtotal_cost += cost
                    chapter.subtotal_sale += sale
                    chapter.subtotal_benefits = (
                        chapter.subtotal_sale - chapter.subtotal_cost)

        for line in self.line_ids:
            tmpl = line.chapter_tmpl_id
            self.total_costs += line.subtotal_cost
            sum_chapter(tmpl.id, cost=line.subtotal_cost)
            for parent in tmpl.get_parents():
                sum_chapter(parent.id, cost=line.subtotal_cost)
        for line in self.simulation_line_ids:
            tmpl = line.line_id.chapter_tmpl_id
            self.total_sales += line.subtotal_sale
            sum_chapter(tmpl.id, sale=line.subtotal_sale)
            if not tmpl.exists():
                continue
            for parent in tmpl.get_parents():
                sum_chapter(parent.id, sale=line.subtotal_sale)
        self.total_benefits = (self.total_sales - self.total_costs)

        self.total_untaxed = self.total_sales
        tax = self.tax_ids.compute_all(self.total_sales, 1)
        self.total_tax = tax['total_included'] - self.total_untaxed
        self.total = tax['total_included']

        # _log.info('='*100)
        # _log.info(('untaxed', self.total_sales))
        # _log.info(('taxs', tax['total_included'] - self.total_untaxed))
        # _log.info(('self.total_tax', self.total_tax))
        # _log.info(('total', tax['total_included']))
        # _log.info('='*100)
