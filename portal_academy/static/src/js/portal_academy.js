/** @odoo-module */

import publicWidget from 'web.public.widget';
import { jsonrpc } from '@web/core/network/rpc_service';
import 'portal.portal'; // force dependencies

publicWidget.registry.PortalHomeCounters.include({
    /**
     * @override
     */
    _getCountersAlwaysDisplayed() {
        return this._super(...arguments).concat(['students_count', 'absence_count', 'bulletin_count', 'enrollment_count']);
    },
});

publicWidget.registry.PortalNewEnrollment = publicWidget.Widget.extend({

    selector: '#enrollment_form',

    events: {
        'change input[name="has_allergy"]': '_onAllergyChange',
        'change input[name="apa_member"]': '_onApaMemberChange',
        'change select[name="student_id"]': '_onStudentSelect',
        'change select[name="training_plan_id"]': '_onTrainingPlanChange',
    },

    start() {
        this.apaBox = this.el.querySelector('#apa_number_box');
        this.apaCheckbox = this.el.querySelector('input[name="apa_member"]');
        if (this.apaCheckbox && this.apaCheckbox.checked) {
            this._showApaBox();
        } else {
            this._hideApaBox();
        }
        this.allergyBox = this.el.querySelector('#allergy_box');
        this.allergyCheckbox = this.el.querySelector('input[name="has_allergy"]');

        if (this.allergyCheckbox && this.allergyCheckbox.checked) {
            this._showAllergyBox();
        } else {
            this._hideAllergyBox();
        }
        this.studentSelect = this.el.querySelector('select[name="student_id"]');
        this.birthInput = this.el.querySelector('input[name="birthdate_date"]');
        this.academicTrainingSelect = this.el.querySelector('select[name="academic_training_id"]');
        const raw = this.studentSelect.dataset.students || '[]';
        this.studentsData = JSON.parse(raw);
        return this._super(...arguments);
    },
    _onStudentSelect(ev) {
        const studentId = parseInt(ev.currentTarget.value);

        if (!studentId) {
            this._resetStudentFields();
            return;
        }

        const student = this.studentsData.find(s => s.id === studentId);
        if (!student) {
            this._resetStudentFields();
            return;
        }

        // --- Fill birthdate ---
        if (this.birthInput) {
            this.birthInput.value = student.birthdate || '';
        }

        // --- Correct way: select academic training via value ---
        if (this.academicTrainingSelect) {
            const academicTrainingId = student.academic_training_ids[0] || '';
            this.academicTrainingSelect.value = academicTrainingId ? String(academicTrainingId) : '';
        }
    },

    _resetStudentFields() {
        if (this.birthInput) {
            this.birthInput.value = '';
        }
        if (this.academicTrainingSelect) {
            this.academicTrainingSelect.value = '';
        }
    },

    // -------------------------------------------------------------------------
    // APA member toggle
    // -------------------------------------------------------------------------
    _onApaMemberChange(ev) {
        if (ev.currentTarget.checked) {
            this._showApaBox();
        } else {
            this._hideApaBox(true);
        }
    },

    _showApaBox() {
        if (this.apaBox) {
            this.apaBox.classList.remove('d-none');
        }
    },

    _hideApaBox(clear) {
        if (this.apaBox) {
            this.apaBox.classList.add('d-none');
            if (clear) {
                const input = this.apaBox.querySelector('input[name="apa_member_number"]');
                if (input) {
                    input.value = '';
                }
            }
        }
    },

    _onAllergyChange(ev) {
        if (ev.currentTarget.checked) {
            this._showAllergyBox();
        } else {
            this._hideAllergyBox(true);
        }
    },

    _showAllergyBox() {
        if (this.allergyBox) {
            this.allergyBox.classList.remove('d-none');
        }
    },

    _hideAllergyBox(clear) {
        if (this.allergyBox) {
            this.allergyBox.classList.add('d-none');
            if (clear) {
                const input = this.allergyBox.querySelector('textarea[name="allergy_description"]');
                if (input) {
                    input.value = '';
                }
            }
        }
    },

    _onTrainingPlanChange(ev) {
        const selectedPlan = ev.currentTarget.value;
        const options = this.el.querySelectorAll('select[name="activity_id"] option');

        options.forEach(opt => {
            const planId = opt.dataset.training_plan_id;
            if (!planId || !selectedPlan) {
                opt.classList.add('d-none');
                opt.removeAttribute('selected');
                return;
            }
            if (planId === selectedPlan) {
                opt.classList.remove('d-none');
            } else {
                opt.classList.add('d-none');
                opt.removeAttribute('selected');
            }
        });

        const activitySelect = this.el.querySelector('select[name="activity_id"]');
        if (activitySelect) {
            activitySelect.value = '';
        }
    },

});
