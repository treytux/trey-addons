/** @odoo-module */

import spreadsheet from "@spreadsheet/o_spreadsheet/o_spreadsheet_extended";
import { EnvDataSource } from "../env_datasource";

const DATA_SOURCE_ID = "SPREADSHEET_ENV";

export default class EnvPlugin extends spreadsheet.UIPlugin {
    constructor(getters, history, dispatch, config) {
        super(getters, history, dispatch, config);
        this.dataSources = config.dataSources;
        if (this.dataSources) {
            this.dataSources.add(DATA_SOURCE_ID, EnvDataSource);
        }
    }

    getEnvSum(model, field, domain) {
        return (
            this.dataSources &&
            this.dataSources.get(DATA_SOURCE_ID).getSum(model, field, domain)
        );
    }

    getEnvAvg(model, field, domain) {
        return (
            this.dataSources &&
            this.dataSources.get(DATA_SOURCE_ID).getAvg(model, field, domain)
        );
    }

    getEnvCount(model, domain) {
        return (
            this.dataSources &&
            this.dataSources.get(DATA_SOURCE_ID).getCount(model, domain)
        );
    }

    getEnvMin(model, field, domain) {
        return (
            this.dataSources &&
            this.dataSources.get(DATA_SOURCE_ID).getMin(model, field, domain)
        );
    }

    getEnvMax(model, field, domain) {
        return (
            this.dataSources &&
            this.dataSources.get(DATA_SOURCE_ID).getMax(model, field, domain)
        );
    }
}

EnvPlugin.getters = [
    "getEnvSum",
    "getEnvAvg",
    "getEnvCount",
    "getEnvMin",
    "getEnvMax",
];
