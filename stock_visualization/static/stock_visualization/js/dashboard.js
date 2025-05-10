document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners to date range buttons
    document.querySelectorAll('[data-range]').forEach(button => {
        button.addEventListener('click', function() {
            const range = this.getAttribute('data-range');
            fetchPortfolioComparison(range);
        });
    });
    
    // Load initial data with 3-month range
    fetchPortfolioComparison('3M');
});

// Function to calculate date range
function getDateRange(range) {
    const endDate = new Date();
    let startDate = new Date();
    
    switch(range) {
        case '1D':
            startDate.setDate(endDate.getDate() - 1);
            break;
        case '1W':
            startDate.setDate(endDate.getDate() - 7);
            break;
        case '1M':
            startDate.setMonth(endDate.getMonth() - 1);
            break;
        case '3M':
            startDate.setMonth(endDate.getMonth() - 3);
            break;
        case '6M':
            startDate.setMonth(endDate.getMonth() - 6);
            break;
        case 'YTD':
            startDate = new Date(endDate.getFullYear(), 0, 1); // January 1st of current year
            break;
        case '1Y':
            startDate.setFullYear(endDate.getFullYear() - 1);
            break;
        case '3Y':
            startDate.setFullYear(endDate.getFullYear() - 3);
            break;
        case '5Y':
            startDate.setFullYear(endDate.getFullYear() - 5);
            break;
        case 'MAX':
            startDate = null; // No start date limit
            break;
        default:
            startDate.setMonth(endDate.getMonth() - 1); // Default to 1 month
    }
    
    return {
        startDate: startDate ? formatDate(startDate) : null,
        endDate: formatDate(endDate)
    };
}

// Format date as YYYY-MM-DD for API
function formatDate(date) {
    return date.toISOString().split('T')[0];
}

// Global variable to keep track of the chart instance
let comparisonChart = null;

function fetchPortfolioComparison(range) {
    // Set the active button
    document.querySelectorAll('[data-range]').forEach(btn => {
        btn.classList.remove('active', 'btn-primary');
        btn.classList.add('btn-outline-primary');
    });
    
    const activeButton = document.querySelector(`[data-range="${range}"]`);
    if (activeButton) {
        activeButton.classList.remove('btn-outline-primary');
        activeButton.classList.add('active', 'btn-primary');
    }
    
    const ctx = document.getElementById('portfolioComparisonChart').getContext('2d');
    const chartContainer = document.getElementById('portfolioComparisonChart').parentNode;
    chartContainer.classList.add('position-relative');
    
    // If there's an existing loading indicator, remove it
    const existingLoader = chartContainer.querySelector('.chart-loader');
    if (existingLoader) {
        existingLoader.remove();
    }
    
    // IMPORTANT: Destroy existing chart before creating a new one
    if (comparisonChart) {
        comparisonChart.destroy();
        comparisonChart = null;
    }
    
    // Add loading indicator
    const loader = document.createElement('div');
    loader.className = 'chart-loader position-absolute top-0 start-0 w-100 h-100 d-flex justify-content-center align-items-center bg-white bg-opacity-75';
    loader.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
    chartContainer.appendChild(loader);
    
    // Calculate date range
    const { startDate, endDate } = getDateRange(range);
    
    // Build URL with query parameters
    let url = `/api/portfolios/history/?end_date=${endDate}`;
    if (startDate) {
        url += `&start_date=${startDate}`;
    }
    
    // Fetch portfolio growth data from API
    fetch(url)
        .then(response => response.json())
        .then(data => {
            // Remove loading indicator
            loader.remove();
            
            // Check if we have data
            if (data.labels && data.labels.length > 0 && data.datasets && data.datasets.length > 0) {
                // Create the real chart
                comparisonChart = new Chart(ctx, {
                    type: 'line',
                    data: data,
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        aspectRatio: 2, // Reduce from 2.5 to 2 for better height
                        plugins: {
                            legend: {
                                position: 'top',
                            },
                            tooltip: {
                                mode: 'index',
                                intersect: false,
                                callbacks: {
                                    label: function(context) {
                                        let label = context.dataset.label || '';
                                        if (label) {
                                            label += ': ';
                                        }
                                        if (context.parsed.y !== null) {
                                            label += new Intl.NumberFormat('en-US', {
                                                style: 'currency',
                                                currency: 'USD'
                                            }).format(context.parsed.y);
                                        }
                                        return label;
                                    }
                                }
                            },
                            title: {
                                display: false
                            }
                        },
                        scales: {
                            x: {
                                display: true,
                                title: {
                                    display: true,
                                    text: 'Date'
                                }
                            },
                            y: {
                                display: true,
                                title: {
                                    display: true,
                                    text: 'Portfolio Value ($)'
                                },
                                ticks: {
                                    callback: function(value) {
                                        return '$' + value.toLocaleString();
                                    }
                                }
                            }
                        },
                        interaction: {
                            intersect: false,
                            mode: 'index',
                        }
                    }
                });
            } else {
                // Handle no data
                const noDataMsg = document.createElement('div');
                noDataMsg.className = 'alert alert-info';
                noDataMsg.textContent = 'No portfolio comparison data available for this date range.';
                
                // Clear the chart container and show message
                chartContainer.innerHTML = '';
                chartContainer.appendChild(noDataMsg);
            }
        })
        .catch(error => {
            // Remove loading indicator
            loader.remove();
            
            console.error('Error loading portfolio comparison data:', error);
            
            // Show error state
            const errorMsg = document.createElement('div');
            errorMsg.className = 'alert alert-danger';
            errorMsg.textContent = 'Error loading data. Please try again later.';
            
            // Clear the chart container and show error
            chartContainer.innerHTML = '';
            chartContainer.appendChild(errorMsg);
        });
}
