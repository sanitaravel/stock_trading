document.addEventListener('DOMContentLoaded', function() {
    // Initialize all charts
    initAllocationChart();
    initPositionPerformanceChart();
    
    // Add event listeners to date range buttons for portfolio history chart
    document.querySelectorAll('[data-range]').forEach(button => {
        button.addEventListener('click',
             function() {
            const range = this.getAttribute('data-range');
            fetchPortfolioHistory(range);
        });
    });
    
    // Load initial data with 3-month range
    fetchPortfolioHistory('3M');
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
let portfolioHistoryChart = null;

// Fetch portfolio history with date range
function fetchPortfolioHistory(range) {
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
    
    const ctx = document.getElementById('portfolioHistoryChart').getContext('2d');
    const chartContainer = document.getElementById('portfolioHistoryChart').parentNode;
    chartContainer.classList.add('position-relative');
    
    // If there's an existing loading indicator, remove it
    const existingLoader = chartContainer.querySelector('.chart-loader');
    if (existingLoader) {
        existingLoader.remove();
    }
    
    // IMPORTANT: Destroy existing chart before creating a new one
    if (portfolioHistoryChart) {
        portfolioHistoryChart.destroy();
        portfolioHistoryChart = null;
    }
    
    // Add loading indicator
    const loader = document.createElement('div');
    loader.className = 'chart-loader position-absolute top-0 start-0 w-100 h-100 d-flex justify-content-center align-items-center bg-white bg-opacity-75';
    loader.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
    chartContainer.appendChild(loader);
    
    // Calculate date range
    const { startDate, endDate } = getDateRange(range);
    
    // Build URL with query parameters
    let url = `/api/portfolio/${portfolioId}/history/?end_date=${endDate}`;
    if (startDate) {
        url += `&start_date=${startDate}`;
    }
    
    // Fetch data from API
    fetch(url)
        .then(response => response.json())
        .then(data => {
            // Remove loading indicator
            loader.remove();
            
            // Check if we have data
            if (data.labels && data.labels.length > 0) {
                // Use the provided initial value which is now reliably stored in the database
                const initialValue = data.initial_value;
                const barColors = data.values.map(value => 
                    value >= initialValue ? 'rgba(40, 167, 69, 0.7)' : 'rgba(220, 53, 69, 0.7)'
                );
                
                const borderColors = data.values.map(value => 
                    value >= initialValue ? 'rgba(40, 167, 69, 1)' : 'rgba(220, 53, 69, 1)'
                );
                
                // Create new bar chart
                portfolioHistoryChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: 'Portfolio Value',
                            // Transform data to show difference from initial value
                            data: data.values.map(value => value - initialValue),
                            backgroundColor: data.values.map(value => 
                                value >= initialValue ? 'rgba(40, 167, 69, 0.7)' : 'rgba(220, 53, 69, 0.7)'
                            ),
                            borderColor: data.values.map(value => 
                                value >= initialValue ? 'rgba(40, 167, 69, 1)' : 'rgba(220, 53, 69, 1)'
                            ),
                            borderWidth: 1,
                            // Store the actual values for tooltips
                            actualValues: data.values
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        aspectRatio: 2,
                        plugins: {
                            tooltip: {
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
                                        let label = context.dataset.label || '';
                                        if (label) {
                                            label += ': ';
                                        }
                                        
                                        // Get the actual value (not the difference)
                                        const actualValue = context.dataset.actualValues[context.dataIndex];
                                        const formatted = new Intl.NumberFormat('en-US', {
                                            style: 'currency',
                                            currency: 'USD'
                                        }).format(actualValue);
                                        
                                        // Add comparison with initial investment
                                        const diff = actualValue - initialValue;
                                        const diffFormatted = new Intl.NumberFormat('en-US', {
                                            style: 'currency',
                                            currency: 'USD',
                                            signDisplay: 'always'
                                        }).format(diff);
                                        
                                        const percentChange = ((actualValue - initialValue) / initialValue * 100).toFixed(2);
                                        
                                        return [
                                            `${label}${formatted}`,
                                            `vs Initial: ${diffFormatted} (${percentChange}%)`
                                        ];
                                    }
                                }
                            },
                            legend: {
                                display: false
                            },
                            title: {
                                display: false
                            }
                        },
                        scales: {
                            x: {
                                grid: {
                                    display: false
                                },                                ticks: {
                                    callback: function(value, index) {
                                        // Format x-axis date labels
                                        const label = this.getLabelForValue(value);
                                        const allLabels = this.chart.data.labels;
                                        
                                        // Use smart date formatting for consistent display
                                        return window.formatChartDateSmart(label, index, allLabels);
                                    }
                                }
                            },
                            y: {
                                beginAtZero: true, // Start from zero for gain/loss visualization
                                grid: {
                                    color: 'rgba(0, 0, 0, 0.1)'
                                },
                                ticks: {
                                    callback: function(value) {
                                        // Format y-axis values to show the difference
                                        return new Intl.NumberFormat('en-US', {
                                            style: 'currency',
                                            currency: 'USD',
                                            signDisplay: 'always'
                                        }).format(value);
                                    }
                                }
                            }
                        },
                        // Add custom plugin to show the "zero" line representing initial investment
                        plugins: [{
                            afterDraw: function(chart) {
                                const ctx = chart.ctx;
                                const yAxis = chart.scales.y;
                                const xAxis = chart.scales.x;
                                
                                // Draw horizontal line at zero (initial investment baseline)
                                const zeroLineY = yAxis.getPixelForValue(0);
                                
                                ctx.save();
                                ctx.beginPath();
                                ctx.moveTo(xAxis.left, zeroLineY);
                                ctx.lineTo(xAxis.right, zeroLineY);
                                ctx.lineWidth = 2;
                                ctx.strokeStyle = 'rgba(0, 0, 0, 0.5)';
                                ctx.setLineDash([5, 5]);
                                ctx.stroke();
                                
                                // Add label for the baseline
                                ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
                                ctx.textAlign = 'left';
                                ctx.textBaseline = 'bottom';
                                ctx.font = '12px Arial';
                                ctx.fillText('Initial Investment: ' + new Intl.NumberFormat('en-US', {
                                    style: 'currency',
                                    currency: 'USD'
                                }).format(initialValue), xAxis.left + 5, zeroLineY - 5);
                                ctx.restore();
                            }
                        }]
                    }
                });
            } else {
                // Handle no data
                const noDataMsg = document.createElement('div');
                noDataMsg.className = 'alert alert-info';
                noDataMsg.textContent = 'No portfolio history data available for this date range.';
                
                // Clear the chart container and show message
                chartContainer.innerHTML = '';
                chartContainer.appendChild(noDataMsg);
            }
        })
        .catch(error => {
            // Remove loading indicator
            loader.remove();
            
            console.error('Error loading portfolio history data:', error);
            
            // Show error message
            const errorMsg = document.createElement('div');
            errorMsg.className = 'alert alert-danger';
            errorMsg.textContent = 'Error loading portfolio history data.';
            
            // Clear the chart container and show error
            chartContainer.innerHTML = '';
            chartContainer.appendChild(errorMsg);
        });
}

function initAllocationChart() {
    const ctx = document.getElementById('allocationChart').getContext('2d');
    
    // Process position data for the pie chart
    const labels = positionData.map(pos => pos.stock_symbol);
    const values = positionData.map(pos => pos.current_value);
    
    // Generate background colors
    const colors = generateColors(positionData.length);
    
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true, // Changed from false to true for better responsive behavior
            aspectRatio: 1.5, // Add proper aspect ratio for pie chart
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        boxWidth: 12
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw;
                            const total = context.dataset.data.reduce((acc, curr) => acc + curr, 0);
                            const percentage = Math.round((value / total) * 100);
                            
                            return `${label}: $${value.toLocaleString()} (${percentage}%)`;
                        }
                    }
                },
                title: {
                    display: false
                }
            }
        }
    });
}

function initPositionPerformanceChart() {
    const ctx = document.getElementById('positionPerformanceChart').getContext('2d');
    
    // Process position data for the bar chart
    const labels = positionData.map(pos => pos.stock_symbol);
    const performances = positionData.map(pos => pos.performance);
    
    // Generate colors based on performance (green for positive, red for negative)
    const colors = performances.map(perf => 
        perf >= 0 ? 'rgba(40, 167, 69, 0.7)' : 'rgba(220, 53, 69, 0.7)'
    );
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Performance (%)',
                data: performances,
                backgroundColor: colors,
                borderColor: colors.map(color => color.replace('0.7', '1')),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true, // Changed from false to true for better responsive behavior
            aspectRatio: 2, // Add proper aspect ratio for bar chart
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const performance = context.raw;
                            return `Performance: ${performance >= 0 ? '+' : ''}${performance.toFixed(2)}%`;
                        }
                    }
                },
                title: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
}

// Helper function to generate consistent colors for charts
function generateColors(count) {
    const baseColors = [
        'rgba(78, 115, 223, 0.7)',
        'rgba(28, 200, 138, 0.7)',
        'rgba(54, 185, 204, 0.7)',
        'rgba(246, 194, 62, 0.7)',
        'rgba(231, 74, 59, 0.7)',
        'rgba(111, 66, 193, 0.7)',
        'rgba(90, 92, 105, 0.7)',
        'rgba(32, 201, 151, 0.7)',
        'rgba(102, 16, 242, 0.7)',
        'rgba(253, 126, 20, 0.7)'
    ];
    
    const colors = [];
    for (let i = 0; i < count; i++) {
        colors.push(baseColors[i % baseColors.length]);
    }
    
    return colors;
}
