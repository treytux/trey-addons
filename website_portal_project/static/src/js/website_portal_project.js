(function() {
    'use strict';

    openerp.website_portal_check_active_tab = {
        dom_ready: $.Deferred(),
        ready: function(){
            return this.dom_ready.then(function() {}).promise();
        },
        init: function(){
            this.dom_ready.resolve();
            if($('[name=account-content-nav] li.active').length == 0){
                $('[name=account-content-nav] li').first().addClass('active');
                $('[name=account-content] .tab-pane').first().addClass('in active');
            }
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
        if($('[name=account-content-nav]').length){
            openerp.website_portal_check_active_tab.init();
        }
    });

}());
