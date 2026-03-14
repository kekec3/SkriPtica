
const fileInput = document.getElementById('file');
const fileUploadDesign = document.querySelector('.file-upload-design');

fileInput.addEventListener('change', function() {
    if (this.files && this.files.length > 0) {
        const fileName = this.files[0].name;
        // Update the UI to show the file name instead of "Drag and Drop"
        fileUploadDesign.innerHTML = `
            <svg viewBox="0 0 384 512" height="1em" style="fill: #28a745;">
                <path d="M0 64C0 28.7 28.7 0 64 0H224V128c0 17.7 14.3 32 32 32H384V448c0 35.3-28.7 64-64 64H64c-35.3 0-64-28.7-64-64V64zm384 64H256V0L384 128z"/>
            </svg>
            <p style="color: #28a745; font-weight: bold;">${fileName}</p>
            <span class="browse-button" style="background: #6c757d;">Promeni fajl</span>
        `;
    }
});