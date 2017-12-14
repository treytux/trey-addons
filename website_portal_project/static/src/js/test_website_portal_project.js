(function(){
    'use strict';
    console.log("ejecuntando");

    openerp.Tour.register({
        id: 'website_portal_project',
        name: 'Website Portal Project',
        path: '/my/projects/',
        mode: 'test',
        steps: [
            {
                waitNot:   '.popover.tour',
                element:   'button[data-action=edit]',
                placement: 'bottom',
                title:     _t("Edit this page"),
                content:   _t("Every page of your website can be modified through the <i>Edit</i> button."),
                popover:   { fixed: true },
            },
        ],
    });
}());
