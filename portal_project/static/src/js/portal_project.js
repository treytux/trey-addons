odoo.define('portal_project.ProjectTasks', function (require) {
    'use strict'
    require('web.dom_ready')
    let Class = require('web.Class')
    let ProjectTasks = Class.extend({
        dom_ready: $.Deferred(),
        ready: function(){
            return this.dom_ready.then(function() {}).promise()
        },
        init: function () {
            this.dom_ready.resolve()
            let $graph_timesheets = $('.js_pp_graph_timesheets')
            if($graph_timesheets.length > 0){
                this.load_chart(
                    this.bar_chart(),
                    JSON.parse($graph_timesheets.attr('graph-data'))
                )
            }
        },
        bar_chart: function(){
            var chart = nv.models.discreteBarChart()
                .x(function(d) { return d.text })
                .y(function(d) { return d.count })
                .staggerLabels(true)
                .showValues(true)
            chart.tooltip.enabled(false)
            return chart
        },
        load_chart: function(chart, response){
            d3.select('.js_pp_graph_timesheets svg')
                .datum(response)
                .transition().duration(500).call(chart)
            nv.utils.windowResize(chart.update)
        }
    })
    let project_tasks = new ProjectTasks()
    return {
        ProjectTasks: ProjectTasks,
        project_tasks: project_tasks,
    }
})
