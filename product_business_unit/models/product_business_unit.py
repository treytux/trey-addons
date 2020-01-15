###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.release import version
from dateutil.relativedelta import relativedelta
from datetime import date
from babel.dates import format_date
import json


class ProductBusinessUnit(models.Model):
    _name = 'product.business.unit'
    _description = 'Product Business Unit'

    name = fields.Char(
        string='Name',
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.user.company_id.id,
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='User',
    )
    area_ids = fields.One2many(
        comodel_name='product.business.area',
        inverse_name='unit_id',
        string='Areas'
    )
    color = fields.Integer(
        string='Color Index',
        help='The color of the channel')
    favorite_user_ids = fields.Many2many(
        comodel_name='res.users',
        relation='product_business_unit2favorite',
        column1='unit_id',
        column2='user_id',
        default=lambda self: [(6, 0, [self.env.uid])],
    )
    is_favorite = fields.Boolean(
        string='Show on dashboard',
        compute='_compute_is_favorite',
        inverse='_inverse_is_favorite',
        help='Favorite teams to display them in the dashboard and access '
             'them easily.',
    )
    dashboard_graph_data = fields.Text(
        compute='_compute_dashboard_graph',
    )
    dashboard_graph_model = fields.Selection(
        selection=[],
        string='Content',
        help='The graph this channel will display in the Dashboard.\n',
    )
    dashboard_graph_group = fields.Selection(
        selection=[
            ('day', 'Day'),
            ('week', 'Week'),
            ('month', 'Month'),
            ('user', 'User'),
        ],
        string='Group by',
        default='day',
        help='How this channel\'s dashboard graph will group the results.',
    )
    dashboard_graph_type = fields.Selection(
        selection=[
            ('line', 'Line'),
            ('bar', 'Bar'),
        ],
        string='Type',
        compute='_compute_dashboard_graph',
        help='The type of graph this channel will display in the dashboard.',
    )
    dashboard_graph_period_pipeline = fields.Selection(
        selection=[
            ('week', 'Within a Week'),
            ('month', 'Within a Month'),
            ('year', 'Within a Year'),
        ],
        string='Expected to Close',
        help='The time period this channel\'s dashboard graph will consider.',
        compute='_compute_dashboard_graph_period_pipeline',
        inverse='_inverse_dashboard_graph_period_pipeline',
    )
    dashboard_graph_period = fields.Selection(
        selection=[
            ('week', 'Within a Week'),
            ('month', 'Within a Month'),
            ('year', 'Within a Year'),
        ],
        string='Scale',
        default='month',
        help='The time period this channel\'s dashboard graph will consider.',
    )

    def force_integrity_unit_and_area(self, vals, actual_area=False):
        if not vals.get('unit_id') and not vals.get('area_id'):
            return {}
        if not vals.get('area_id'):
            if not actual_area or actual_area.unit_id.id != vals['unit_id']:
                return {'area_id': False}
            vals['area_id'] = actual_area.id
        area_id = self.env['product.business.area'].browse(vals['area_id'])
        if not vals.get('unit_id'):
            return {'unit_id': area_id.unit_id.id}
        unit_id = self.browse(vals['unit_id'])
        if unit_id != area_id.unit_id:
            return {'area_id': False}
        return {}

    def _compute_is_favorite(self):
        for unit in self:
            unit.is_favorite = self.env.user in unit.favorite_user_ids

    def _inverse_is_favorite(self):
        sudoed_self = self.sudo()
        to_fav = sudoed_self.filtered(
            lambda team: self.env.user not in team.favorite_user_ids)
        to_fav.write({'favorite_user_ids': [(4, self.env.uid)]})
        (sudoed_self - to_fav).write({
            'favorite_user_ids': [(3, self.env.uid)]})
        return True

    def _compute_dashboard_graph_period_pipeline(self):
        for unit in self:
            unit.dashboard_graph_period_pipeline = unit.dashboard_graph_period

    def _inverse_dashboard_graph_period_pipeline(self):
        units = self.filtered(lambda u: u.dashboard_graph_model == 'crm.lead')
        for unit in units:
            unit.dashboard_graph_period = unit.dashboard_graph_period_pipeline

    @api.depends('dashboard_graph_group', 'dashboard_graph_model',
                 'dashboard_graph_period')
    def _compute_dashboard_graph(self):
        for unit in self.filtered('dashboard_graph_model'):
            if unit.dashboard_graph_period in ['day']:
                unit.dashboard_graph_type = 'bar'
            else:
                unit.dashboard_graph_type = 'line'
            unit.dashboard_graph_data = json.dumps(unit._get_graph())

    def _get_graph(self):
        def get_week_name(start_date, locale):
            if (start_date + relativedelta(days=6)).month == start_date.month:
                short_name_from = format_date(start_date, 'd', locale=locale)
            else:
                short_name_from = format_date(
                    start_date, 'd MMM', locale=locale)
            short_name_to = format_date(
                start_date + relativedelta(days=6), 'd MMM', locale=locale)
            return short_name_from + '-' + short_name_to

        self.ensure_one()
        values = []
        today = fields.Date.from_string(fields.Date.context_today(self))
        start_date, end_date = self._graph_get_dates(today)
        graph_data = self._graph_data(start_date, end_date)
        if self.dashboard_graph_type == 'line':
            x_field = 'x'
            y_field = 'y'
        else:
            x_field = 'label'
            y_field = 'value'
        locale = self._context.get('lang') or 'en_US'
        if self.dashboard_graph_group == 'day':
            for day in range(0, (end_date - start_date).days + 1):
                short_name = format_date(
                    start_date + relativedelta(days=day), 'd MMM',
                    locale=locale)
                values.append({x_field: short_name, y_field: 0})
            for data_item in graph_data:
                index = (data_item.get('x_value') - start_date).days
                values[index][y_field] = data_item.get('y_value')
        elif self.dashboard_graph_group == 'week':
            weeks_in_start_year = int(
                date(start_date.year, 12, 28).isocalendar()[1])
            weeks = range(0, (
                end_date.isocalendar()[1] - start_date.isocalendar()[1]) %
                weeks_in_start_year + 1)
            for week in weeks:
                short_name = get_week_name(
                    start_date + relativedelta(days=7 * week), locale)
                values.append({x_field: short_name, y_field: 0})
            for data_item in graph_data:
                index = int(
                    (data_item.get('x_value') - start_date.isocalendar()[1]) %
                    weeks_in_start_year)
                values[index][y_field] = data_item.get('y_value')
        elif self.dashboard_graph_group == 'month':
            months = range(0, (end_date.month - start_date.month) % 12 + 1)
            for month in months:
                short_name = format_date(
                    start_date + relativedelta(months=month), 'MMM',
                    locale=locale)
                values.append({x_field: short_name, y_field: 0})
            for data_item in graph_data:
                index = int((data_item.get('x_value') - start_date.month) % 12)
                values[index][y_field] = data_item.get('y_value')
        else:
            for data_item in graph_data:
                values.append({
                    x_field: data_item.get('x_value'),
                    y_field: data_item.get('y_value')})
        [graph_title, graph_key] = self._graph_title_and_key()
        color = '#875A7B' if '+e' in version else '#7c7bad'
        return [{
            'values': values,
            'area': True,
            'title': graph_title,
            'key': graph_key,
            'color': color}]

    def _graph_get_dates(self, today):
        if self.dashboard_graph_period == 'week':
            start_date = today - relativedelta(weeks=1)
        elif self.dashboard_graph_period == 'year':
            start_date = today - relativedelta(years=1)
        else:
            start_date = today - relativedelta(months=1)
        if self.dashboard_graph_group == 'month':
            start_date = date(
                start_date.year + start_date.month // 12,
                start_date.month % 12 + 1, 1)
            if self.dashboard_graph_period == 'week':
                start_date = today.replace(day=1)
        elif self.dashboard_graph_group == 'week':
            start_date += relativedelta(days=8 - start_date.isocalendar()[2])
            if self.dashboard_graph_period == 'year':
                start_date += relativedelta(weeks=1)
        else:
            start_date += relativedelta(days=1)
        return [start_date, today]

    def _graph_data(self, start_date, end_date):
        query = '''SELECT %(x_query)s as x_value, %(y_query)s as y_value
                     FROM %(table)s
                    WHERE unit_id = %(unit_id)s
                      AND DATE(%(date_column)s) >= %(start_date)s
                      AND DATE(%(date_column)s) <= %(end_date)s
                      %(extra_conditions)s
                    GROUP BY x_value;'''
        if not self.dashboard_graph_model:
            raise UserError(
                _('Undefined graph model for Business Unit: %s') % self.name)
        model = self.env[self.dashboard_graph_model]
        graph_table = model._table
        extra_conditions = self._extra_sql_conditions()
        where_query = model._where_calc([])
        model._apply_ir_rules(where_query, 'read')
        from_clause, where_clause, where_clause_params = where_query.get_sql()
        if where_clause:
            extra_conditions += ' AND ' + where_clause
        query = query % {
            'x_query': self._graph_x_query(),
            'y_query': self._graph_y_query(),
            'table': graph_table,
            'unit_id': "%s",
            'date_column': self._graph_date_column(),
            'start_date': "%s",
            'end_date': "%s",
            'extra_conditions': extra_conditions
        }
        self._cr.execute(
            query, [self.id, start_date, end_date] + where_clause_params)
        return self.env.cr.dictfetchall()

    def _extra_sql_conditions(self):
        return ''

    def _graph_date_column(self):
        return 'create_date'

    def _graph_x_query(self):
        if self.dashboard_graph_group == 'user':
            return 'user_id'
        elif self.dashboard_graph_group == 'week':
            return 'EXTRACT(WEEK FROM %s)' % self._graph_date_column()
        elif self.dashboard_graph_group == 'month':
            return 'EXTRACT(MONTH FROM %s)' % self._graph_date_column()
        return 'DATE(%s)' % self._graph_date_column()

    def _graph_y_query(self):
        raise UserError(
            _('Undefined graph model for Business Unit: %s') % self.name)

    def _graph_title_and_key(self):
        if self.dashboard_graph_model == 'crm.lead':
            return ['', _('Pipeline: Expected Revenue')]
        return super()._graph_title_and_key()
