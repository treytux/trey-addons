/** @odoo-module */

import spreadsheet from "@spreadsheet/o_spreadsheet/o_spreadsheet_extended";
import EnvPlugin from "./plugins/env_plugin";
import "./env_functions";

const { uiPluginRegistry } = spreadsheet.registries;

uiPluginRegistry.add("odooEnvAggregates", EnvPlugin);
