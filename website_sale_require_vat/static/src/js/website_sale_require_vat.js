(function () {
    'use strict';

    openerp.website_sale_require_vat = {
        dom_ready: $.Deferred(),
        ready: function(){
            return this.dom_ready.then(function() {}).promise();
        },
        init: function(){
            this.dom_ready.resolve();

            var wsrv_vat = $( 'body[data-view-xmlid="website_sale.checkout"] input[name="vat"]' );

            if(wsrv_vat.length == 1) {
                wsrv_vat.closest('form').on('submit', function(e){
                    openerp.website_sale_require_vat.check_vat( wsrv_vat );
                });
            }
        },
        check_vat: function( wsrv_vat ){
            var wsrv_vat_value = '';
            var wsrv_country_code = 'ES';
            var wsrv_vat_country_code = '';

            wsrv_vat_value = wsrv_vat.val().trim().toUpperCase();
            wsrv_vat.val(wsrv_vat_value);
            wsrv_vat_country_code = wsrv_vat_value.substr(0, 2);
            if(wsrv_vat_value != '' &&  wsrv_vat_country_code != wsrv_country_code) {
                wsrv_vat.val(wsrv_country_code + wsrv_vat.val());
            }
        }
    }

    $(document).ready(function () {
        if( $('body[data-oe-xmlid="website_sale.checkout"] input[name="vat"]').length == 1) {
            openerp.website_sale_require_vat.init();
        }
    });

})();
