/** @odoo-module **/

import ajax from 'web.ajax';
import publicWidget from 'web.public.widget';

publicWidget.registry.AddressLocationAutocomplete = publicWidget.Widget.extend({
    selector: '.o_address_location_autocomplete',

    events: {
        'input [data-location-search]': '_onSearchInput',
        'change': '_onManualAddressChange',
        'click [data-location-id]': '_onLocationSelect',
    },

    start() {
        this.searchInput = this.el.querySelector('[data-location-search]');
        this.results = this.el.querySelector('[data-location-results]');
        this.locationInput = this._getField('location');
        this.searchTimeout = false;
        this.applyingLocation = false;
        return this._super(...arguments);
    },

    _getField(type) {
        const fieldName = this.el.dataset[`${type}Field`];
        return fieldName
            ? this.el.querySelector(`[name="${fieldName}"]`)
            : null;
    },

    _getCountryId() {
        const country = this._getField('country');
        return country ? country.value : false;
    },

    _onSearchInput(ev) {
        const search = ev.currentTarget.value.trim();
        clearTimeout(this.searchTimeout);
        this._clearLocationId();
        if (search.length < 2) {
            this._hideResults();
            return;
        }
        this.searchTimeout = setTimeout(() => {
            ajax.jsonRpc('/address_location_autocomplete/search', 'call', {
                search,
                country_id: this._getCountryId(),
            }).then(locations => this._renderResults(locations));
        }, 250);
    },

    _onLocationSelect(ev) {
        const location = JSON.parse(ev.currentTarget.dataset.location);
        const country = this._getField('country');
        const state = this._getField('state');
        const city = this._getField('city');
        const zip = this._getField('zip');

        this.applyingLocation = true;
        if (this.locationInput) this.locationInput.value = location.id;
        this.searchInput.value = location.label;
        if (city) city.value = location.city;
        if (zip) zip.value = location.zip;
        if (country) country.value = location.country_id;
        if (state) {
            state.querySelectorAll('option[data-country_id]').forEach(option => {
                option.style.display = option.dataset.country_id ===
                    String(location.country_id) ? '' : 'none';
            });
            state.value = location.state_id || '';
        }
        this.applyingLocation = false;
        this._hideResults();
    },

    _onManualAddressChange() {
        if (!this.applyingLocation) this._clearLocationId();
    },

    _clearLocationId() {
        if (this.locationInput) this.locationInput.value = '';
    },

    _renderResults(locations) {
        this.results.innerHTML = '';
        locations.forEach(location => {
            const option = document.createElement('button');
            option.type = 'button';
            option.className = 'list-group-item list-group-item-action';
            option.dataset.locationId = location.id;
            option.dataset.location = JSON.stringify(location);
            option.textContent = location.label;
            this.results.appendChild(option);
        });
        this.results.classList.toggle('d-none', !locations.length);
    },

    _hideResults() {
        this.results.innerHTML = '';
        this.results.classList.add('d-none');
    },
});
