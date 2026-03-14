const categoryInput = document.querySelector('input[name="kategorija"]');

const resultsBox = document.createElement('div');
resultsBox.className = 'search-results-box'; // You'll need CSS for this (see below)
categoryInput.parentNode.style.position = 'relative';
categoryInput.parentNode.appendChild(resultsBox);

categoryInput.addEventListener('input', function() {
    const query = this.value;

    if (query.length < 1) {
        resultsBox.style.display = 'none';
        return;
    }

    fetch(`/materials/api/categories/?q=${query}`)
        .then(response => response.json())
        .then(data => {
            resultsBox.innerHTML = '';
            if (data.length > 0) {
                data.forEach(item => {
                    const div = document.createElement('div');
                    div.className = 'result-item';
                    div.style.padding = '10px';
                    div.style.cursor = 'pointer';
                    div.style.border = '1.5px solid #000';
                    div.style.background = 'white';
                    div.style.marginBottom = '2px';
                    div.textContent = item.name;

                    div.addEventListener('click', () => {
                        categoryInput.value = item.name;

                        const hiddenInput = document.getElementById('selected-category-id');
                        if (hiddenInput) {
                            hiddenInput.value = item.id;
                            console.log("Category ID set to:", item.id); // Check console to verify
                        }

                        resultsBox.style.display = 'none';

                        document.getElementById('selected-category-id').value = item.id;
                        categoryInput.setAttribute('data-id', item.id);
                        resultsBox.style.display = 'none';
                    });
                    resultsBox.appendChild(div);
                });
                resultsBox.style.display = 'block';
            } else {
                resultsBox.style.display = 'none';
            }
        });
});