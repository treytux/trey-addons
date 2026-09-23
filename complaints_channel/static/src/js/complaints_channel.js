document.addEventListener('DOMContentLoaded', function () {
    const url_complaints = window.location.pathname
    if (url_complaints.includes('complaints_channel/complaint')) {
        const anonymous_complaint = document.getElementById('anonymous')
        const evidence_file_complaint = document.getElementById('evidence_file')
        const file_label_complaint = document.getElementById('evidence_file_label')
        const name_complaint = document.getElementById('first_name')
        const last_name_complaint = document.getElementById('last_name')
        const filename_original = file_label_complaint.innerText
        anonymous_complaint.addEventListener('change', function () {
            if (anonymous_complaint.checked) {
                name_complaint.disabled = true
                last_name_complaint.disabled = true
            } else {
                name_complaint.disabled = false
                last_name_complaint.disabled = false
            }
        })
        evidence_file_complaint.addEventListener('change', function () {
            if (evidence_file_complaint.files.length > 0) {
                const filename_complaints = evidence_file_complaint.files[0].name
                file_label_complaint.innerText = filename_complaints
            } else {
                file_label_complaint.innerText = filename_original
            }
        })
    }
})
function limpiarURLs() {
    setTimeout(() => {
        limpiarURL()
    }, 2000);
}
function limpiarURL() {
    const nuevaURL = window.location.protocol + '//' + window.location.host + window.location.pathname;
    history.replaceState({}, document.title, nuevaURL);
}

setInterval(limpiarURLs, 2000);
