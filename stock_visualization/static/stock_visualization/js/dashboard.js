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
                // Process datasets to ensure straight lines
                data.datasets.forEach(dataset => {
                    dataset.lineTension = 0; // Set tension to 0 for straight lines
                    dataset.tension = 0;     // Newer Chart.js versions use this property
                });
                
                // Sort datasets by the latest data point (richest to poorest)
                data.datasets.sort((a, b) => {
                    const aLastValue = a.data[a.data.length - 1] || 0;
                    const bLastValue = b.data[b.data.length - 1] || 0;
                    return bLastValue - aLastValue; // Descending order
                });
                
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
                                position: 'right',
                                align: 'center',
                                labels: {
                                    boxWidth: 12,
                                    padding: 10,
                                    usePointStyle: true,
                                    pointStyle: 'circle',
                                    // Sort legend labels to match the dataset order (already sorted)
                                    sort: null // Using null to preserve our custom sort order
                                },
                                // Make legend more compact
                                display: true,
                                maxHeight: 50,
                                maxWidth: 800
                            },
                            tooltip: {
                                mode: 'index',
                                intersect: false,
                                callbacks: {
                                    title: function(tooltipItems) {
                                        // Format the tooltip title (date) to be more readable
                                        if (tooltipItems.length > 0) {
                                            const dateStr = tooltipItems[0].label;
                                            const date = new Date(dateStr);
                                            return date.toLocaleDateString(undefined, { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' });
                                        }
                                        return '';
                                    },
                                    label: function(context) {
                                        // Get the dataset label (short name)
                                        let label = context.dataset.label || '';
                                        
                                        // Find matching portfolio in portfolioData
                                        const portfolio = portfolioData.find(p => 
                                            p.short_name === label || p.name === label
                                        );
                                        
                                        // Show full portfolio name in tooltip for clarity
                                        let displayLabel = (portfolio?.name || label) + ': ';
                                        
                                        if (context.parsed.y !== null) {
                                            // Format the current value
                                            const currentValue = new Intl.NumberFormat('en-US', {
                                                style: 'currency',
                                                currency: 'USD'
                                            }).format(context.parsed.y);
                                            
                                            displayLabel += currentValue;
                                            
                                            // If we have initial price data, show the performance
                                            if (portfolio && portfolio.initial_price) {
                                                const initialPrice = parseFloat(portfolio.initial_price);
                                                const currentPrice = context.parsed.y;
                                                const performancePercent = ((currentPrice - initialPrice) / initialPrice * 100).toFixed(2);
                                                const performanceValue = new Intl.NumberFormat('en-US', {
                                                    style: 'currency',
                                                    currency: 'USD',
                                                    signDisplay: 'always'
                                                }).format(currentPrice - initialPrice);
                                                
                                                // Add a second line with performance data
                                                return [displayLabel, `Change: ${performanceValue} (${performancePercent}%)`];
                                            }
                                        }
                                        return displayLabel;
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
                                },
                                ticks: {
                                    callback: function(value, index) {
                                        // Format x-axis date labels
                                        const label = this.getLabelForValue(value);
                                        const date = new Date(label);
                                        
                                        // Different formatting based on date range
                                        if (data.labels.length > 30) {
                                            // For longer periods, just show month/year
                                            return date.toLocaleDateString(undefined, { month: 'short', year: '2-digit' });
                                        } else {
                                            // For shorter periods, show day/month
                                            return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
                                        }
                                    },
                                    maxRotation: 45,
                                    minRotation: 0
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
