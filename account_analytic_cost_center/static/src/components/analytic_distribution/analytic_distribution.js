/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { AnalyticDistribution } from "@analytic/components/analytic_distribution/analytic_distribution";
import { SelectCreateDialog } from "@web/views/view_dialogs/select_create_dialog";


patch(AnalyticDistribution.prototype, "analytic_distribution_cost_center", {

    newTag(group_id) {
        var options = this._super.apply(this, arguments);
        options.analytic_cost_center_id = null;
        options.analytic_cost_center_name = '';
        return options;
    },

    async fetchAnalyticCostCenter(domain, limit=null) {
        const args = {
            domain: domain,
            fields: ["id", "name"],
            context: [],
        }
        if (limit) {
            args['limit'] = limit;
        }
        if (domain.length === 1 && domain[0][0] === "id") {
            return await this.props.record.model.orm.read("account.analytic.cost_center", domain[0][2], args.fields, {});
        }
        return await this.orm.call("account.analytic.cost_center", "search_read", [], args);
    },

    sourcesAnalyticCostCenters(dist_tag) {
        if (dist_tag.analytic_account_id === null) {
            return [];
        }
        return [
            {
                placeholder: this.env._t("Loading..."),
                options:(searchTerm) => this.loadOptionsSourceCostCenter(searchTerm),
            }
        ];
    },

    async loadOptionsSourceCostCenter(searchTerm) {
        let domain = [];
        if (this.props.record.data.company_id){
            domain.push(
                '|',
                ['company_id', '=', this.props.record.data.company_id[0]],
                ['company_id', '=', false],
            );
        }
        let searchDomain = [
            ['name', 'ilike', searchTerm],
        ];
        const searchLimit = 6;
        const records = await this.fetchAnalyticCostCenter(
            [...domain, ...searchDomain], searchLimit + 1);
        let options = records.map((result) => ({
            value: result.id,
            label: result.name,
        }));
        if (searchLimit < records.length) {
            options.push({
                label: this.env._t('Search More...'),
                action: (editedTag) => this.onSearchMoreCostCenter(searchTerm ?? '', editedTag),
                classList: 'o_m2o_dropdown_option o_m2o_dropdown_option_search_more',
            });
        }
        if (!options.length) {
            options.push({
                label: this.env._t('No cost centers'),
                classList: 'o_m2o_no_result',
                unselectable: true,
            });
        }
        return options;
    },

    async onSelect(option, params, tag) {
        await this._super.apply(this, arguments);
        this.setFocusSelector(`.tag_${tag.id} .o_analytic_cost_center`);
    },

    async onSelectCostCenter(option, params, tag) {
        if (option.action) {
            return option.action(tag);
        }
        if (tag.analytic_account_id === null) {
            tag.analytic_cost_center_id = null;
            tag.analytic_cost_center_name = '';
            return;
        }
        const selected_option = Object.getPrototypeOf(option);
        tag.analytic_cost_center_id = parseInt(selected_option.value);
        tag.analytic_cost_center_name = selected_option.label;
        this.setFocusSelector(`.tag_${tag.id} .o_analytic_percentage`);
        this.autoFill();
    },

    async onSearchMoreCostCenter(searchTerm, editedTag) {
        let dynamicFilters = [];
        if (searchTerm.length) {
            dynamicFilters = [
                {
                    description: sprintf(this.env._t("Quick search: %s"), searchTerm),
                    domain: this.searchAnalyticDomain(searchTerm),
                },
            ];
        }
        this.selectCreateIsOpen = true;
        this.addDialog(SelectCreateDialog, {
            title: this.env._t("Search: Analytic Center Cost"),
            noCreate: true,
            multiSelect: false,
            resModel: 'account.analytic.cost_center',
            context: {
                tree_view_ref: "account_analytic_cost_center.account_analytic_cost_center_tree",
            },
            domain: [],
            dynamicFilters: dynamicFilters,
            onSelected: async (resIds) => {
                const cost_centers = await this.fetchAnalyticCostCenter([["id", "=", resIds]]);
                editedTag.analytic_cost_center_id = cost_centers[0].id;
                editedTag.analytic_cost_center_name = cost_centers[0].name;
                this.setFocusSelector(`.tag_${editedTag.id} .o_analytic_percentage`);
                this.autoFill();
            },
            onCreateEdit: () => {},
        }, {
            onClose: () => {
                if (!editedTag.analytic_cost_center_id) {
                    this.setFocusSelector(`.tag_${editedTag.id} .o_analytic_cost_center`);
                    this.focusToSelector();
                }
                this.selectCreateIsOpen = false;
            },
        });
    },

    async formatData(nextProps) {
        await this._super.apply(this, arguments);
        for (let root_plan_id in this.state.list) {
            let distribution = nextProps.record.data.analytic_distribution_cost_center ?? {};
            let ids = Object.values(distribution).filter(item => item !== null)
            let records = Object.entries(distribution).length !== 0 ? await this.fetchAnalyticCostCenter([["id", "in", ids]]) : [];
            records = Object.fromEntries(records.map(record => [record.id, record]));
            for(const index in this.state.list[root_plan_id].distribution) {
                let analytic_account_id = this.state.list[root_plan_id].distribution[index].analytic_account_id;
                let cost_center = records[distribution[analytic_account_id]] ?? {id: null, name: '', };
                let data = {
                    analytic_cost_center_name: cost_center.name,
                    analytic_cost_center_id: cost_center.id,
                };
                this.state.list[root_plan_id].distribution[index] = Object.assign({}, this.state.list[root_plan_id].distribution[index], data);
            }
        }
    },

    async save() {
        await this._super.apply(this, arguments);
        let data = {};
        for (let root_plan_id in this.state.list) {
            for(const index in this.state.list[root_plan_id].distribution) {
                if (this.state.list[root_plan_id].distribution[index].analytic_cost_center_id === null) {
                    continue;
                }
                data[this.state.list[root_plan_id].distribution[index].analytic_account_id] = this.state.list[root_plan_id].distribution[index].analytic_cost_center_id;
            }
        }
        await this.props.record.update({
            ['analytic_distribution_cost_center']: data,
        });
    },


});
