(function() {
    'use strict';

    openerp.website_portal_contract_graph = {
        dom_ready: $.Deferred(),
        ready: function(){
            return this.dom_ready.then(function() {}).promise();
        },
        init: function(){
            this.dom_ready.resolve();
            this.load_chart(
                this.bar_chart(),
                JSON.parse($('#graph_timesheet').attr('graph-data')),
                35);
        },
        bar_chart: function(){
            return nv.models.discreteBarChart()
                .x(function(d) { return d.text; })
                .y(function(d) { return d.count; })
                .staggerLabels(true)
                .tooltips(false)
                .showValues(true);
        },
        load_chart: function(chart, response){
            d3.select('#graph_timesheet svg')
                .datum(response)
                .transition().duration(500).call(chart);
            nv.utils.windowResize(chart.update);
        }
    };

    openerp.website.if_dom_contains('.o_my_show_more', function() {
        $('.o_my_show_more').on('click', function(ev) {
            ev.preventDefault();
            $(this).parents('table').find(".to_hide").toggleClass('hidden');
            $(this).find('span').toggleClass('hidden');
        });

    });

    $(document).ready(function () {
        if($('.o_my_graph').length){
            openerp.website_portal_contract_graph.init();
        }
    });

}());
