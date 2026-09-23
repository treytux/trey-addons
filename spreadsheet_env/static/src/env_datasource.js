/** @odoo-module */

import { ServerData } from "@spreadsheet/data_sources/server_data";

export class EnvDataSource {
    constructor(services) {
        this.serverData = new ServerData(services.orm, {
            whenDataIsFetched: () => services.notify(),
        });
    }

    getSum(model, field, domain) {
        const data = this.serverData.batch.get(
            "spreadsheet.env",
            "spreadsheet_env_sum",
            [model, field, domain]
        );
        if (data) {
            return data.value || 0;
        }
        return 0;
    }

    getAvg(model, field, domain) {
        const data = this.serverData.batch.get(
            "spreadsheet.env",
            "spreadsheet_env_avg",
            [model, field, domain]
        );
        if (data) {
            return data.value || 0;
        }
        return 0;
    }

    getCount(model, domain) {
        const data = this.serverData.batch.get(
            "spreadsheet.env",
            "spreadsheet_env_count",
            [model, domain]
        );
        if (data) {
            return data.value || 0;
        }
        return 0;
    }

    getMin(model, field, domain) {
        const data = this.serverData.batch.get(
            "spreadsheet.env",
            "spreadsheet_env_min",
            [model, field, domain]
        );
        if (data) {
            return data.value || 0;
        }
        return 0;
    }

    getMax(model, field, domain) {
        const data = this.serverData.batch.get(
            "spreadsheet.env",
            "spreadsheet_env_max",
            [model, field, domain]
        );
        if (data) {
            return data.value || 0;
        }
        return 0;
    }
}
