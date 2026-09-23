odoo.define('complaints_channel.Complaint', function (require) {
    'use strict'
    require('web.dom_ready')
    let Class = require('web.Class')
    let Complaint = Class.extend({
        dom_ready: $.Deferred(),
        ready: function(){
            return this.dom_ready.then(function() {}).promise()
        },
        start: function () {
            return this._super.apply(this, arguments)
        },
        init: function () {
            this.dom_ready.resolve()
            const url_complaints = window.location.pathname
            if (url_complaints.includes('/complaints_channel/complaint')) {
                const anonymous_complaint = document.getElementById('anonymous')
                const evidence_file_complaint = document.getElementById('evidence_file')
                const file_label_complaint = document.getElementById('evidence_file_label')
                const name_complaint = document.getElementById('first_name')
                const last_name_complaint = document.getElementById('last_name')
                if (!anonymous_complaint || !evidence_file_complaint) return
                const filename_original = file_label_complaint?.innerText || ''
                anonymous_complaint.addEventListener('change', function () {
                    name_complaint.disabled = anonymous_complaint.checked
                    last_name_complaint.disabled = anonymous_complaint.checked
                })
                evidence_file_complaint.addEventListener('change', function () {
                    if (evidence_file_complaint.files.length > 0) {
                        file_label_complaint.innerText = evidence_file_complaint.files[0].name
                    } else {
                        file_label_complaint.innerText = filename_original
                    }
                })
            }
        },
    })
    let complaint = new Complaint()
    return {
        Complaint: Complaint,
        complaint: complaint,
    }
})
