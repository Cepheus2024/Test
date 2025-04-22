/**
 * User Dashboard JavaScript
 * Handles functionality for the user dashboard and related pages
 */

// Initialize the user dashboard functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard charts
    initializeDashboardCharts();
    
    // Initialize quiz timer
    initializeQuizTimer();
    
    // Initialize quiz submission
    initializeQuizSubmission();
});

/**
 * Initializes dashboard charts
 */
function initializeDashboardCharts() {
    const performanceChartElement = document.getElementById('performanceChart');
    const subjectChartElement = document.getElementById('subjectPerformanceChart');
    
    if (performanceChartElement || subjectChartElement) {
        // Fetch performance data
        fetch('/user/api/performance-data')
            .then(response => response.json())
            .then(data => {
                if (performanceChartElement) {
                    renderPerformanceChart(performanceChartElement, data.performance_over_time);
                }
                
                if (subjectChartElement) {
                    renderSubjectChart(subjectChartElement, data.subject_performance);
                }
            })
            .catch(error => {
                console.error('Error loading performance data:', error);
                if (performanceChartElement) {
                    performanceChartElement.innerHTML = '<div class="alert alert-danger">Failed to load performance data</div>';
                }
                if (subjectChartElement) {
                    subjectChartElement.innerHTML = '<div class="alert alert-danger">Failed to load subject performance data</div>';
                }
            });
    }
}

/**
 * Renders performance over time chart
 * @param {HTMLElement} element - The canvas element
 * @param {Object} data - The performance data
 */
function renderPerformanceChart(element, data) {
    const ctx = element.getContext('2d');
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Average Score',
                data: data.data,
                borderColor: '#0dcaf0',
                backgroundColor: 'rgba(13, 202, 240, 0.1)',
                borderWidth: 2,
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Score: ${context.parsed.y.toFixed(2)}%`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

/**
 * Renders subject performance chart
 * @param {HTMLElement} element - The canvas element
 * @param {Object} data - The subject performance data
 */
function renderSubjectChart(element, data) {
    const ctx = element.getContext('2d');
    
    // Generate colors for each subject
    const colors = [];
    for (let i = 0; i < data.labels.length; i++) {
        const hue = (i * 137) % 360; // Golden angle approximation for color distribution
        colors.push(`hsl(${hue}, 70%, 60%)`);
    }
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Average Score',
                data: data.data,
                backgroundColor: colors,
                borderColor: colors.map(color => color.replace('0.2', '1')),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Score: ${context.parsed.y.toFixed(2)}%`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

/**
 * Initializes quiz timer functionality
 */
function initializeQuizTimer() {
    const timerElement = document.getElementById('quizTimer');
    const quizForm = document.getElementById('quizForm');
    const timeInput = document.getElementById('time_taken');
    
    if (timerElement && quizForm) {
        const duration = parseInt(timerElement.getAttribute('data-duration'), 10) || 60;
        let timeRemaining = duration * 60; // Convert to seconds
        let timeTaken = 0;
        
        // Update timer every second
        const timerInterval = setInterval(function() {
            if (timeRemaining <= 0) {
                clearInterval(timerInterval);
                alert('Time is up! Submitting your quiz...');
                submitQuiz();
                return;
            }
            
            timeRemaining--;
            timeTaken++;
            
            // Update timer display
            const minutes = Math.floor(timeRemaining / 60);
            const seconds = timeRemaining % 60;
            timerElement.textContent = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
            
            // Update warning class based on time remaining
            if (timeRemaining < 60) { // Less than 1 minute
                timerElement.classList.add('text-danger');
                timerElement.classList.remove('text-warning');
            } else if (timeRemaining < 300) { // Less than 5 minutes
                timerElement.classList.add('text-warning');
                timerElement.classList.remove('text-danger');
            }
            
            // Update hidden time taken input
            if (timeInput) {
                timeInput.value = timeTaken;
            }
        }, 1000);
        
        // Function to submit the quiz
        function submitQuiz() {
            if (timeInput) {
                timeInput.value = timeTaken;
            }
            quizForm.submit();
        }
        
        // Handle form submission
        quizForm.addEventListener('submit', function() {
            clearInterval(timerInterval);
        });
    }
}

/**
 * Initializes quiz submission functionality
 */
function initializeQuizSubmission() {
    const quizForm = document.getElementById('quizForm');
    
    if (quizForm) {
        quizForm.addEventListener('submit', function(e) {
            // Check if at least one option is selected for each question
            const questions = document.querySelectorAll('.question-container');
            let allAnswered = true;
            
            questions.forEach(question => {
                const questionId = question.getAttribute('data-question-id');
                const options = document.querySelectorAll(`input[name="question_${questionId}"]:checked`);
                
                if (options.length === 0) {
                    question.classList.add('border-danger');
                    allAnswered = false;
                } else {
                    question.classList.remove('border-danger');
                }
            });
            
            if (!allAnswered) {
                e.preventDefault();
                alert('Please answer all questions before submitting.');
                window.scrollTo(0, 0);
            }
        });
    }
}

/**
 * Initializes export functionality
 */
function initializeExport() {
    const exportButton = document.getElementById('exportHistoryBtn');
    
    if (exportButton) {
        exportButton.addEventListener('click', function() {
            alert('Export job started. You will receive an email with the CSV file shortly.');
        });
    }
}
