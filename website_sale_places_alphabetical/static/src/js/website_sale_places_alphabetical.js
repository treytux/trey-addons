(function () {
    'use strict';

    openerp.wspa_order_places = {
        dom_ready: $.Deferred(),
        ready: function(){
            return this.dom_ready.then(function() {}).promise();
        },
        init: function(){
            this.dom_ready.resolve();
            openerp.wspa_order_places.order_select( 'select[name="country_id"]' );
            openerp.wspa_order_places.order_select( 'select[name="state_id"]' );
        },
        order_select: function( selector ){
            var wspa_select = $( selector );
            if( wspa_select.length > 0 ) {
                var wspa_options = $( selector + ' option[value!=""]');
                if( wspa_options.length > 0 ) {
                    var wspa_empty_options = $( selector + ' option[value=""]');
                    var wspa_selected = wspa_select.val();
                    wspa_options.sort(function(a,b) {
                        if( a.text.toLowerCase() > b.text.toLowerCase() ) return 1;
                        else if ( a.text.toLowerCase() < b.text.toLowerCase() ) return -1;
                        else return 0
                    });
                    wspa_select.empty();
                    if( wspa_empty_options.length > 0 ) {
                        wspa_select.append( wspa_empty_options );
                    }
                    wspa_select.append( wspa_options );
                    wspa_select.val( wspa_selected );
                }
            }
        }
    }

    $(document).ready(function () {
        openerp.wspa_order_places.init();
    });

})();
