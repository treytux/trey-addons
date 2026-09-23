odoo.define('web_view_calendar_day.CalendarDayController', function (require) {
    'use strict'

    let Core = require('web.core')
    let QWeb = Core.qweb
    var config = require('web.config')
    var AbstractController = require('web.AbstractController')

    function updateDate(to, date){
        if(to == 'prev'){
            date.setDate(date.getDate() - 1)
        } else if (to == 'next') {
            date.setDate(date.getDate() + 1)
        } else if (to == 'today') {
            let current_date = new Date()
            date.setTime(current_date.getTime())
        }
        date.setHours(0)
        date.setMinutes(0)
        date.setSeconds(0)
        return date
    }

    var CalendarDayController = AbstractController.extend({
        init: function (parent, model, renderer, params) {
            let self = this
            self._super.apply(this, arguments)
        },
        _move: function (to, date_to) {
            let date
            if (this.model.domain.length > 0){
                let has_date_end = false
                this.model.domain.forEach(function (domain){
                    if (Array.isArray(domain)){
                        domain.forEach(function (field){
                            if (field == 'date_end'){
                                if (date_to){
                                    date = new Date(date_to)
                                } else {
                                    date = new Date(domain[2])
                                }
                                has_date_end = true
                                date = updateDate(to, date)
                                domain[2] = date
                            }
                        })
                    }
                })
                if(!has_date_end){
                    let array = []
                    array.push('date_end')
                    array.push('>=')
                    date = new Date(date_to)
                    date = updateDate(to, date)
                    array.push(date)
                    this.model.domain.push(array)
                }
            } else if (this.model.domain.length == 0){
                this.model.domain = []
                this.model.domain[0] = '&'
                this.model.domain[1] = []
                this.model.domain[1][0] = 'state'
                this.model.domain[1][1] = '!='
                this.model.domain[1][2] = 'cancel'
                this.model.domain[2] = []
                this.model.domain[2][0] = 'date_end'
                this.model.domain[2][1] = '>='
                date = new Date(date_to)
                date.setHours(0)
                date.setMinutes(0)
                date.setSeconds(0)
                date = updateDate(to, date)
                this.model.domain[2][2] = date
            }
            return this.reload()
        },
        renderButtons: function ($node) {
            var self = this
            this.$buttons = $(QWeb.render('web_view_calendar_day.buttons', {
                isMobile: config.device.isMobile,
            }))
            _.each(['prev', 'today', 'next'], function (action) {
                self.$buttons.on('click', '.o_calendar_button_' + action, function () {
                    let date_to = document.getElementById("date_selection").value
                    self._move(action, date_to)
                })
            })
            _.each(['date_selection'], function (action) {
                self.$buttons.on('click', '.o_calendar_button_' + action, function () {
                    this.$date = $(QWeb.render('web_view_calendar_day.buttons', {
                        isMobile: config.device.isMobile,
                    }))
                    let date_to = document.getElementById("date_selection").value
                    self._move(action, date_to)
                })
            })
            this.$buttons.find('.o_calendar_button_' + this.mode).addClass('active')
            if ($node) {
                this.$buttons.appendTo($node)
            } else {
                this.$('.o_calendar_buttons').replaceWith(this.$buttons)
            }
        },
    })
    return CalendarDayController
})
