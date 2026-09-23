odoo.define('portal_hr_timesheet_stats.StatsEmployee', function (require) {
    'use strict'
    require('web.dom_ready')
    let Class = require('web.Class')
    let StatsEmployee = Class.extend({
        dom_ready: $.Deferred(),
        ready: function(){
            return this.dom_ready.then(function() {}).promise()
        },
        init: function () {
            this.dom_ready.resolve()
            let chart_selector = 'o_phts_chart'
            let $productivity_chart = $('#' + chart_selector)
            if($productivity_chart.length > 0){
                let context = document.getElementById(chart_selector).getContext('2d')
                let chart = new Chart(context, {
                    'type': 'bar',
                    'data': JSON.parse($productivity_chart.attr('chart-data')),
                    options: {
                        plugins: {
                            legend: {
                                display: true,
                            }
                        },
                        interaction: {
                            intersect: false,
                        },
                        scales: {
                            x: {
                                stacked: true,
                            },
                            y: {
                                stacked: true
                            }
                        },
                        responsive: true
                    }
                })
            }
        },
    })
    let stats_employee = new StatsEmployee()
    return {
        StatsEmployee: StatsEmployee,
        stats_employee: stats_employee,
    }
})
