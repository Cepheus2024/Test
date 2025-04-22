/**
 * Admin Dashboard JavaScript
 * Handles functionality for the admin dashboard and related pages
 */

// Initialize the admin dashboard functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize search functionality
    initializeSearch();
    
    // Initialize subject management
    initializeSubjectManagement();
    
    // Initialize chapter management
    initializeChapterManagement();
    
    // Initialize quiz management
    initializeQuizManagement();
    
    // Initialize question management
    initializeQuestionManagement();
    
    // Initialize user management
    initializeUserManagement();
    
    // Initialize reports
    initializeReports();
});

/**
 * Initializes search functionality
 */
function initializeSearch() {
    const searchForm = document.getElementById('adminSearchForm');
    const searchInput = document.getElementById('adminSearch');
    
    if (searchForm && searchInput) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const query = searchInput.value.trim();
            
            if (query) {
                // Show loading indicator
                const searchButton = searchForm.querySelector('button[type="submit"]');
                const originalContent = searchButton.innerHTML;
                searchButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Searching...';
                searchButton.disabled = true;
                
                // Perform search via fetch instead of form submission
                fetch('/admin/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-Requested-With': 'XMLHttpRequest' // This helps identify AJAX requests on the server
                    },
                    body: new URLSearchParams({
                        'csrf_token': searchForm.querySelector('input[name="csrf_token"]').value,
                        'q': query
                    })
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    displaySearchResults(query, data);
                })
                .catch(error => {
                    console.error('Search error:', error);
                    alert('An error occurred while searching. Please try again.');
                })
                .finally(() => {
                    // Restore button state
                    searchButton.innerHTML = originalContent;
                    searchButton.disabled = false;
                });
            }
        });
    }
}

/**
 * Displays search results in a modal
 * @param {string} query - The search query
 * @param {Object} data - The search results data
 */
function displaySearchResults(query, data) {
    if (!data.success) {
        alert(data.message || 'An error occurred with your search. Please try again.');
        return;
    }

    const results = data.results;
    
    const modalHtml = `
        <div class="modal fade" id="searchResultsModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content bg-dark">
                    <div class="modal-header">
                        <h5 class="modal-title">Search Results for "${query}"</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <!-- Users -->
                        ${results.users && results.users.length > 0 ? `
                            <h6 class="border-bottom pb-2 mb-3">Users</h6>
                            <ul class="list-group mb-4">
                                ${results.users.map(user => `
                                    <li class="list-group-item bg-dark border-secondary d-flex justify-content-between align-items-center">
                                        <div>
                                            <span class="fw-bold">${user.fullname}</span> 
                                            <small class="text-muted">@${user.username}</small>
                                            <small class="d-block text-muted">${user.email}</small>
                                        </div>
                                        <a href="${user.url}" class="btn btn-sm btn-outline-primary">
                                            <i class="fas fa-eye me-1"></i>View
                                        </a>
                                    </li>
                                `).join('')}
                            </ul>
                        ` : ''}
                        
                        <!-- Subjects -->
                        ${results.subjects && results.subjects.length > 0 ? `
                            <h6 class="border-bottom pb-2 mb-3">Subjects</h6>
                            <ul class="list-group mb-4">
                                ${results.subjects.map(subject => `
                                    <li class="list-group-item bg-dark border-secondary d-flex justify-content-between align-items-center">
                                        <div>
                                            <span class="fw-bold">${subject.name}</span>
                                            <small class="d-block text-muted">${subject.description || 'No description'}</small>
                                            <span class="badge bg-info mt-1">${subject.chapter_count} chapter(s)</span>
                                        </div>
                                        <a href="${subject.url}" class="btn btn-sm btn-outline-primary">
                                            <i class="fas fa-folder-open me-1"></i>View Chapters
                                        </a>
                                    </li>
                                `).join('')}
                            </ul>
                        ` : ''}
                        
                        <!-- Chapters -->
                        ${results.chapters && results.chapters.length > 0 ? `
                            <h6 class="border-bottom pb-2 mb-3">Chapters</h6>
                            <ul class="list-group mb-4">
                                ${results.chapters.map(chapter => `
                                    <li class="list-group-item bg-dark border-secondary d-flex justify-content-between align-items-center">
                                        <div>
                                            <span class="fw-bold">${chapter.name}</span> 
                                            <small class="d-block text-muted">in ${chapter.subject_name}</small>
                                            <small class="d-block text-muted">${chapter.description || 'No description'}</small>
                                            <span class="badge bg-info mt-1">${chapter.quiz_count} quiz(zes)</span>
                                        </div>
                                        <a href="${chapter.url}" class="btn btn-sm btn-outline-primary">
                                            <i class="fas fa-tasks me-1"></i>View Quizzes
                                        </a>
                                    </li>
                                `).join('')}
                            </ul>
                        ` : ''}
                        
                        <!-- Quizzes -->
                        ${results.quizzes && results.quizzes.length > 0 ? `
                            <h6 class="border-bottom pb-2 mb-3">Quizzes</h6>
                            <ul class="list-group mb-4">
                                ${results.quizzes.map(quiz => `
                                    <li class="list-group-item bg-dark border-secondary d-flex justify-content-between align-items-center">
                                        <div>
                                            <span class="fw-bold">${quiz.title}</span>
                                            <small class="d-block text-muted">in ${quiz.chapter_name} (${quiz.subject_name})</small>
                                            <small class="d-block text-muted">${quiz.description || 'No description'}</small>
                                            <span class="badge bg-info mt-1">${quiz.date}</span>
                                        </div>
                                        <a href="${quiz.url}" class="btn btn-sm btn-outline-primary">
                                            <i class="fas fa-edit me-1"></i>Edit
                                        </a>
                                    </li>
                                `).join('')}
                            </ul>
                        ` : ''}
                        
                        <!-- No Results -->
                        ${
                            (!results.users || results.users.length === 0) && 
                            (!results.subjects || results.subjects.length === 0) && 
                            (!results.chapters || results.chapters.length === 0) && 
                            (!results.quizzes || results.quizzes.length === 0) 
                                ? `
                                    <div class="text-center py-4">
                                        <i class="fas fa-search fa-3x mb-3 text-muted"></i>
                                        <p class="lead">No results found for "${query}"</p>
                                        <p class="text-muted">Try different keywords or check your spelling</p>
                                    </div>
                                ` : ''
                        }
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove any existing modal
    const existingModal = document.getElementById('searchResultsModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to DOM
    const modalContainer = document.createElement('div');
    modalContainer.innerHTML = modalHtml;
    document.body.appendChild(modalContainer);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('searchResultsModal'));
    modal.show();
    
    // Clean up when modal is hidden
    document.getElementById('searchResultsModal').addEventListener('hidden.bs.modal', function() {
        document.body.removeChild(modalContainer);
    });
}

/**
 * Initializes subject management functionality
 */
function initializeSubjectManagement() {
    // Edit subject functionality
    const editButtons = document.querySelectorAll('.edit-subject-btn');
    const editForm = document.getElementById('editSubjectForm');
    
    if (editButtons.length && editForm) {
        const editNameInput = document.getElementById('edit_name');
        const editDescriptionInput = document.getElementById('edit_description');
        
        editButtons.forEach(button => {
            button.addEventListener('click', function() {
                const id = this.getAttribute('data-id');
                const name = this.getAttribute('data-name');
                const description = this.getAttribute('data-description');
                
                editForm.action = `/admin/subjects/edit/${id}`;
                editNameInput.value = name;
                editDescriptionInput.value = description;
            });
        });
    }
    
    // Delete subject confirmation
    const deleteButtons = document.querySelectorAll('.delete-subject-btn');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this subject? This will delete all associated chapters, quizzes, and questions.')) {
                e.preventDefault();
            }
        });
    });
}

/**
 * Initializes chapter management functionality
 */
function initializeChapterManagement() {
    // Edit chapter functionality
    const editButtons = document.querySelectorAll('.edit-chapter-btn');
    const editForm = document.getElementById('editChapterForm');
    
    if (editButtons.length && editForm) {
        const editNameInput = document.getElementById('edit_name');
        const editDescriptionInput = document.getElementById('edit_description');
        
        editButtons.forEach(button => {
            button.addEventListener('click', function() {
                const id = this.getAttribute('data-id');
                const name = this.getAttribute('data-name');
                const description = this.getAttribute('data-description');
                
                editForm.action = `/admin/chapters/edit/${id}`;
                editNameInput.value = name;
                editDescriptionInput.value = description;
            });
        });
    }
    
    // Delete chapter confirmation
    const deleteButtons = document.querySelectorAll('.delete-chapter-btn');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this chapter? This will delete all associated quizzes and questions.')) {
                e.preventDefault();
            }
        });
    });
}

/**
 * Initializes quiz management functionality
 */
function initializeQuizManagement() {
    // Date picker polyfill
    const datePickers = document.querySelectorAll('input[type="date"]');
    datePickers.forEach(picker => {
        picker.addEventListener('click', function() {
            if (this.type === 'text') {
                this.type = 'date';
            }
        });
    });
    
    // Edit quiz is handled in edit_quiz.html with separate JavaScript
    
    // Delete quiz confirmation
    const deleteButtons = document.querySelectorAll('.delete-quiz-btn');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this quiz? This will delete all associated questions and attempts.')) {
                e.preventDefault();
            }
        });
    });
    
    // Toggle paid quiz price field
    const isPaidCheckbox = document.getElementById('is_paid');
    const priceField = document.getElementById('price_container');
    
    if (isPaidCheckbox && priceField) {
        isPaidCheckbox.addEventListener('change', function() {
            priceField.style.display = this.checked ? 'block' : 'none';
        });
        
        // Initialize state
        priceField.style.display = isPaidCheckbox.checked ? 'block' : 'none';
    }
}

/**
 * Initializes question management functionality
 */
function initializeQuestionManagement() {
    // Edit question functionality
    const editButtons = document.querySelectorAll('.edit-question-btn');
    
    editButtons.forEach(button => {
        button.addEventListener('click', function() {
            const id = this.getAttribute('data-id');
            const questionStatement = this.getAttribute('data-question');
            const option1 = this.getAttribute('data-option1');
            const option2 = this.getAttribute('data-option2');
            const option3 = this.getAttribute('data-option3');
            const option4 = this.getAttribute('data-option4');
            const correctOption = this.getAttribute('data-correct');
            const marks = this.getAttribute('data-marks');
            
            // Fill the form
            document.getElementById('edit_question_id').value = id;
            document.getElementById('edit_question_statement').value = questionStatement;
            document.getElementById('edit_option1').value = option1;
            document.getElementById('edit_option2').value = option2;
            document.getElementById('edit_option3').value = option3;
            document.getElementById('edit_option4').value = option4;
            document.getElementById('edit_correct_option').value = correctOption;
            document.getElementById('edit_marks').value = marks;
        });
    });
    
    // Delete question confirmation
    const deleteButtons = document.querySelectorAll('.delete-question-btn');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this question?')) {
                e.preventDefault();
            }
        });
    });
}

/**
 * Initializes user management functionality
 */
function initializeUserManagement() {
    // Delete user confirmation
    const deleteButtons = document.querySelectorAll('.delete-user-btn');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this user? This will delete all their quiz attempts.')) {
                e.preventDefault();
            }
        });
    });
}

/**
 * Initializes reports page functionality
 */
function initializeReports() {
    const reportCharts = document.querySelectorAll('.report-chart');
    
    if (reportCharts.length) {
        // Charts will be initialized with specific data in the templates
        console.log('Reports charts ready');
    }
}
