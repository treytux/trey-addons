/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";

import spreadsheet from "@spreadsheet/o_spreadsheet/o_spreadsheet_extended";
const { functionRegistry } = spreadsheet.registries;
const { args, toString } = spreadsheet.helpers;

const ODOO_ENV_ARGS_WITH_FIELD = `
    model (string) ${_t("The technical name of the model (e.g. 'sale.order').")}
    field (string) ${_t("The field name to aggregate (e.g. 'amount_total').")}
    domain (string, optional) ${_t(
        "The domain filter as a string (e.g. \"[('state','=','sale')]\")."
    )}
`;

const ODOO_ENV_ARGS_COUNT = `
    model (string) ${_t("The technical name of the model (e.g. 'sale.order').")}
    domain (string, optional) ${_t(
        "The domain filter as a string (e.g. \"[('state','=','sale')]\")."
    )}
`;

functionRegistry.add("ODOO.ENV.SUM", {
    description: _t("Get the sum of a field for records matching a domain."),
    args: args(ODOO_ENV_ARGS_WITH_FIELD),
    returns: ["NUMBER"],
    compute: function (model, field, domain = "[]") {
        model = toString(model).trim();
        field = toString(field).trim();
        domain = toString(domain).trim();
        return this.getters.getEnvSum(model, field, domain);
    },
    computeFormat: () => "#,##0.00",
});

functionRegistry.add("ODOO.ENV.AVG", {
    description: _t("Get the average of a field for records matching a domain."),
    args: args(ODOO_ENV_ARGS_WITH_FIELD),
    returns: ["NUMBER"],
    compute: function (model, field, domain = "[]") {
        model = toString(model).trim();
        field = toString(field).trim();
        domain = toString(domain).trim();
        return this.getters.getEnvAvg(model, field, domain);
    },
    computeFormat: () => "#,##0.00",
});

functionRegistry.add("ODOO.ENV.COUNT", {
    description: _t("Get the count of records matching a domain."),
    args: args(ODOO_ENV_ARGS_COUNT),
    returns: ["NUMBER"],
    compute: function (model, domain = "[]") {
        model = toString(model).trim();
        domain = toString(domain).trim();
        return this.getters.getEnvCount(model, domain);
    },
    computeFormat: () => "#,##0",
});

functionRegistry.add("ODOO.ENV.MIN", {
    description: _t("Get the minimum value of a field for records matching a domain."),
    args: args(ODOO_ENV_ARGS_WITH_FIELD),
    returns: ["NUMBER"],
    compute: function (model, field, domain = "[]") {
        model = toString(model).trim();
        field = toString(field).trim();
        domain = toString(domain).trim();
        return this.getters.getEnvMin(model, field, domain);
    },
    computeFormat: () => "#,##0.00",
});

functionRegistry.add("ODOO.ENV.MAX", {
    description: _t("Get the maximum value of a field for records matching a domain."),
    args: args(ODOO_ENV_ARGS_WITH_FIELD),
    returns: ["NUMBER"],
    compute: function (model, field, domain = "[]") {
        model = toString(model).trim();
        field = toString(field).trim();
        domain = toString(domain).trim();
        return this.getters.getEnvMax(model, field, domain);
    },
    computeFormat: () => "#,##0.00",
});
