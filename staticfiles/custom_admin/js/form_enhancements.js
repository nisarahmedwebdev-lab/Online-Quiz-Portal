// Form enhancements for better user experience
document.addEventListener('DOMContentLoaded', function() {
    // Auto-focus on first input in forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const firstInput = form.querySelector('input[type="text"], input[type="email"], input[type="number"], select, textarea');
        if (firstInput) {
            firstInput.focus();
        }
    });

    // Confirm before deleting
    const deleteButtons = document.querySelectorAll('a[onclick*="confirm"]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm(this.getAttribute('data-confirm') || 'Are you sure you want to delete this item?')) {
                e.preventDefault();
            }
        });
    });

    // Add character counter for text areas
    const textAreas = document.querySelectorAll('textarea');
    textAreas.forEach(textarea => {
        const maxLength = textarea.getAttribute('maxlength');
        if (maxLength) {
            const counter = document.createElement('div');
            counter.className = 'form-text text-end';
            counter.textContent = `0/${maxLength} characters`;
            
            textarea.parentNode.appendChild(counter);
            
            textarea.addEventListener('input', function() {
                const currentLength = this.value.length;
                counter.textContent = `${currentLength}/${maxLength} characters`;
                
                if (currentLength > maxLength * 0.8) {
                    counter.classList.add('text-warning');
                } else {
                    counter.classList.remove('text-warning');
                }
            });
        }
    });
});