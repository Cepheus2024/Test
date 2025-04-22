/**
 * Chart Utilities
 * Helper functions for creating and managing charts
 */

/**
 * Creates a custom line chart
 * @param {string} elementId - The ID of the canvas element
 * @param {Array} labels - Array of labels for X-axis
 * @param {Array} data - Array of data points
 * @param {string} label - Dataset label
 * @param {Object} options - Additional options for the chart
 * @returns {Chart} The created chart instance
 */
function createLineChart(elementId, labels, data, label, options = {}) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
                position: 'top'
            },
            tooltip: {
                mode: 'index',
                intersect: false
            }
        },
        scales: {
            y: {
                beginAtZero: true,
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
    };
    
    const chartOptions = Object.assign({}, defaultOptions, options);
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                borderColor: options.borderColor || '#0dcaf0',
                backgroundColor: options.backgroundColor || 'rgba(13, 202, 240, 0.1)',
                borderWidth: options.borderWidth || 2,
                tension: options.tension || 0.3,
                fill: options.fill !== undefined ? options.fill : true
            }]
        },
        options: chartOptions
    });
}

/**
 * Creates a bar chart
 * @param {string} elementId - The ID of the canvas element
 * @param {Array} labels - Array of labels for X-axis
 * @param {Array} data - Array of data points
 * @param {string} label - Dataset label
 * @param {Object} options - Additional options for the chart
 * @returns {Chart} The created chart instance
 */
function createBarChart(elementId, labels, data, label, options = {}) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    // Generate colors for each bar
    const colors = [];
    for (let i = 0; i < data.length; i++) {
        const hue = (i * 137) % 360; // Golden angle approximation for color distribution
        colors.push(`hsl(${hue}, 70%, 60%)`);
    }
    
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
                position: 'top'
            },
            tooltip: {
                mode: 'index',
                intersect: false
            }
        },
        scales: {
            y: {
                beginAtZero: true,
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
    };
    
    const chartOptions = Object.assign({}, defaultOptions, options);
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                backgroundColor: options.backgroundColor || colors,
                borderColor: options.borderColor || colors.map(color => color.replace('0.2', '1')),
                borderWidth: options.borderWidth || 1
            }]
        },
        options: chartOptions
    });
}

/**
 * Creates a doughnut/pie chart
 * @param {string} elementId - The ID of the canvas element
 * @param {Array} labels - Array of labels
 * @param {Array} data - Array of data points
 * @param {Object} options - Additional options for the chart
 * @returns {Chart} The created chart instance
 */
function createDoughnutChart(elementId, labels, data, options = {}) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    // Generate colors for each segment
    const colors = [];
    for (let i = 0; i < data.length; i++) {
        const hue = (i * 137) % 360; // Golden angle approximation for color distribution
        colors.push(`hsl(${hue}, 70%, 60%)`);
    }
    
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'right'
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        const label = context.label || '';
                        const value = context.parsed || 0;
                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                        const percentage = Math.round((value / total) * 100);
                        return `${label}: ${value} (${percentage}%)`;
                    }
                }
            }
        }
    };
    
    const chartOptions = Object.assign({}, defaultOptions, options);
    
    return new Chart(ctx, {
        type: options.type || 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: options.backgroundColor || colors,
                borderColor: options.borderColor || '#343a40',
                borderWidth: options.borderWidth || 1
            }]
        },
        options: chartOptions
    });
}

/**
 * Updates a chart with new data
 * @param {Chart} chart - The chart instance to update
 * @param {Array} labels - New labels
 * @param {Array} data - New data
 */
function updateChartData(chart, labels, data) {
    chart.data.labels = labels;
    chart.data.datasets[0].data = data;
    chart.update();
}

/**
 * Formats a number for display
 * @param {number} value - The value to format
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted number
 */
function formatNumber(value, decimals = 2) {
    return parseFloat(value).toFixed(decimals);
}

/**
 * Formats a percentage value
 * @param {number} value - The value (0-1)
 * @returns {string} Formatted percentage
 */
function formatPercentage(value) {
    return (value * 100).toFixed(2) + '%';
}
