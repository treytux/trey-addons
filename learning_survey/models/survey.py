# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api


class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    @api.one
    def calculate_approved(self):
        min_score = self.subscription_id.training_id.exam_id.min_score
        if self.state == 'done':
            self.approved = bool(self.quizz_score >= min_score)

    subscription_id = fields.Many2one(
        comodel_name='learning.subscription',
        string='Subscription',
        required=False)
    approved = fields.Boolean(
        string='Approved',
        compute='calculate_approved')
    page_ids = fields.One2many(
        comodel_name='survey.user_input.page',
        inverse_name='user_input_id',
        string='Pages',
        required=False)


class SurveySurvey(models.Model):
    _inherit = "survey.survey"

    @api.model
    def next_page(self, user_input, page_id, go_back=False):
        if user_input.page_ids:
            survey = user_input.survey_id
            ids = []
            for page in user_input.page_ids:
                ids.append(page.page_id.id)
            pages = self.env['survey.page'].browse(ids)
            pages = list(enumerate(pages))
            # *****************************************************
            # First page
            if page_id == 0:
                return pages[0][1], 0, len(pages) == 1
            current_page_index = pages.index((filter(
                lambda p: p[1].id == page_id, pages))[0])
            # All the pages have been displayed
            if current_page_index == len(pages) - 1 and not go_back:
                return None, -1, False
            # Let's get back, baby!
            elif go_back and survey.users_can_go_back:
                return (pages[current_page_index - 1][1],
                        current_page_index - 1, False)
            else:
                # This will show the last page
                if current_page_index == len(pages) - 2:
                    return (pages[current_page_index + 1][1],
                            current_page_index + 1, True)
                # This will show a regular page
                else:
                    return (pages[current_page_index + 1][1],
                            current_page_index + 1, False)
        else:
            return super(SurveySurvey, self).next_page(
                user_input=user_input, page_id=page_id, go_back=go_back)


class SurveyUserInputPage(models.Model):
    _name = 'survey.user_input.page'
    _description = 'Survey User Input Pages'

    @api.one
    def _calculate_page_number(self):
        pages = list(enumerate(self.user_input_id.page_ids))
        current_page_index = pages.index((filter(
            lambda p: p[1].id == self.id, pages))[0]) + 1
        self.page_number = current_page_index

    user_input_id = fields.Many2one(
        comodel_name="survey.user_input",
        string="User Input",
        required=True)
    survey_id = fields.Many2one(
        comodel_name="survey.survey",
        string="Survey",
        related='user_input_id.survey_id',
        store=True)
    page_id = fields.Many2one(
        comodel_name="survey.page",
        string="Page",
        required=True)
    page_number = fields.Integer(
        string='Page Number',
        compute='_calculate_page_number',
        required=False)
