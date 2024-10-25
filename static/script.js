// Sorting functionality
let currentSort = { column: -1, asc: true };

function sortTable(column) {
    const table = document.getElementById('resultsTable');
    const rows = Array.from(table.getElementsByTagName('tr'));
    const isAsc = currentSort.column === column ? !currentSort.asc : true;

    rows.slice(1).sort((a, b) => {
        const aValue = a.getElementsByTagName('td')[column].textContent;
        const bValue = b.getElementsByTagName('td')[column].textContent;

        if (column === 2) { // Score column
            return isAsc ? parseFloat(aValue) - parseFloat(bValue) : parseFloat(bValue) - parseFloat(aValue);
        }
        return isAsc ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue);
    }).forEach(row => table.appendChild(row));

    currentSort = { column, asc: isAsc };
}

// Pagination functionality
const rowsPerPage = 10;
let currentPage = 1;

function showPage(page) {
    const table = document.getElementById('resultsTable');
    const rows = Array.from(table.getElementsByTagName('tr')).slice(1);
    const start = (page - 1) * rowsPerPage;
    const end = start + rowsPerPage;

    rows.forEach((row, index) => {
        row.style.display = (index >= start && index < end) ? '' : 'none';
    });

    document.getElementById('prevBtn').disabled = page === 1;
    document.getElementById('nextBtn').disabled = end >= rows.length;
}

function previousPage() {
    if (currentPage > 1) {
        currentPage--;
        showPage(currentPage);
    }
}

function nextPage() {
    const table = document.getElementById('resultsTable');
    const rows = table.getElementsByTagName('tr').length - 1;
    if (currentPage * rowsPerPage < rows) {
        currentPage++;
        showPage(currentPage);
    }
}

// Row selection functionality
function toggleAllRows(checkbox) {
    const rowCheckboxes = document.getElementsByClassName('row-checkbox');
    Array.from(rowCheckboxes).forEach(cb => cb.checked = checkbox.checked);
    updateSelectedCount();
}

function updateSelectedCount() {
    const selected = document.getElementsByClassName('row-checkbox');
    const selectedCount = Array.from(selected).filter(cb => cb.checked).length;
    document.getElementById('selectedCount').textContent = selectedCount;
}

// Initialize the table
document.addEventListener('DOMContentLoaded', function() {
    showPage(1);
    updateSelectedCount();
});

// File upload interactions
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.querySelector('.file-input');
    const fileLabel = document.querySelector('.file-label');

    if (fileInput && fileLabel) {
        fileInput.addEventListener('change', function(e) {
            if (!validateFileSize(this)) return;
            const fileName = e.target.files[0]?.name;
            if (fileName) {
                const span = fileLabel.querySelector('span:not(.file-types)');
                span.textContent = fileName;
            }
        });

        // Drag and drop functionality
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            fileLabel.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            fileLabel.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            fileLabel.addEventListener(eventName, unhighlight, false);
        });

        function highlight(e) {
            fileLabel.classList.add('dragover');
        }

        function unhighlight(e) {
            fileLabel.classList.remove('dragover');
        }

        fileLabel.addEventListener('drop', handleDrop, false);

        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            fileInput.files = files;

            const fileName = files[0]?.name;
            if (fileName) {
                const span = fileLabel.querySelector('span:not(.file-types)');
                span.textContent = fileName;
            }
        }
    }
});

function validateFileSize(input) {
    const maxSize = 16 * 1024 * 1024; // 16MB
    const file = input.files[0];

    if (file && file.size > maxSize) {
        alert('File size exceeds 16MB limit');
        input.value = '';
        return false;
    }
    return true;
}

function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const icons = {
        'pdf': 'bi-file-pdf',
        'doc': 'bi-file-word',
        'docx': 'bi-file-word',
        'txt': 'bi-file-text'
    };
    return icons[ext] || 'bi-file';
}

function updateFileLabel(filename) {
    const iconClass = getFileIcon(filename);
    const label = document.querySelector('.file-label');
    label.innerHTML = `
        <i class="bi ${iconClass}"></i>
        <span>${filename}</span>
        <span class="file-types">PDF, DOC, DOCX, TXT</span>
    `;
}
