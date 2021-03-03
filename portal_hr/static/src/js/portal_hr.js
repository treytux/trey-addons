odoo.define('portal_hr.Timesheets', function (require) {
    'use strict'
    require('web.dom_ready')
    let Class = require('web.Class')
    let Timesheets = Class.extend({
        dom_ready: $.Deferred(),
        ready: function(){
            return this.dom_ready.then(function() {}).promise()
        },
        init: function () {
            this.dom_ready.resolve()
            this.load_chart(
                this.bar_chart(),
                JSON.parse($('.js_ph_graph_timesheets').attr('graph-data'))
            )
        },
        bar_chart: function(){
            var chart = nv.models.discreteBarChart()
                .x(function(d) { return d.text })
                .y(function(d) { return d.count })
                .staggerLabels(true)
                .showValues(true)
            chart.tooltip.enabled(false)
            return chart
            // http://nvd3.org/examples/multiBar.html
            // var chart = nv.models.multiBarChart()
            //   .transitionDuration(350)
            //   .reduceXTicks(true)   //If 'false', every single x-axis tick label will be rendered.
            //   .rotateLabels(0)      //Angle to rotate x-axis labels.
            //   .showControls(true)   //Allow user to switch between 'Grouped' and 'Stacked' mode.
            //   .groupSpacing(0.1)    //Distance between each group of bars.
            // chart.xAxis
            //     .tickFormat(d3.format(',f'));
            // chart.yAxis
            //     .tickFormat(d3.format(',.1f'));
            // d3.select('#chart1 svg')
            //     .datum(exampleData())
            //     .call(chart);
            // nv.utils.windowResize(chart.update);
            // return chart

            // function exampleData() {
            //   return stream_layers(3,10+Math.random()*100,.1).map(function(data, i) {
            //     return {
            //       key: 'Stream #' + i,
            //       values: data
            //     };
            //   });
            // }
        },
        load_chart: function(chart, response){
            d3.select('.js_ph_graph_timesheets svg')
                .datum(response)
                .transition().duration(500).call(chart)
            nv.utils.windowResize(chart.update)
        }
    })
    let timesheets = new Timesheets()
    return {
        Timesheets: Timesheets,
        timesheets: timesheets,
    }
})
odoo.define('portal_hr.AssignedTasks', function (require) {
    'use strict'
    require('web.dom_ready')
    let Class = require('web.Class')
    let AssignedTasks = Class.extend({
        dom_ready: $.Deferred(),
        ready: function(){
            return this.dom_ready.then(function() {}).promise()
        },
        init: function () {
            this.dom_ready.resolve()
            this.load_chart(
                this.bar_chart(),
                JSON.parse($('.js_ph_graph_assigned_tasks').attr('graph-data'))
            )
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
            d3.select('.js_ph_graph_assigned_tasks svg')
                .datum(response)
                .transition().duration(500).call(chart)
            nv.utils.windowResize(chart.update)
        }
    })
    let assigned_tasks = new AssignedTasks()
    return {
        AssignedTasks: AssignedTasks,
        assigned_tasks: assigned_tasks,
    }
})
