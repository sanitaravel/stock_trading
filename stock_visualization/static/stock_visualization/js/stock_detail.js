document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('priceChart').getContext('2d');
    const stockId = document.getElementById('priceChart').getAttribute('data-stock-id');
    let chart;
    
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
    
    // Initialize chart
    function initChart() {
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Close Price',
                    data: [],
                    borderColor: 'var(--bs-primary, #0d6efd)',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    tension: 0, // Straight lines
                    fill: true,
                    pointRadius: 2,
                    pointHoverRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 2.5,
                plugins: {
                    legend: {
                        display: true,
                        labels: {
                            color: getComputedStyle(document.documentElement).getPropertyValue('--bs-body-color') || '#333'
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            title: function(tooltipItems) {
                                if (tooltipItems.length > 0) {
                                    const dateStr = tooltipItems[0].label;
                                    const date = new Date(dateStr);
                                    return date.toLocaleDateString(undefined, { 
                                        weekday: 'short', 
                                        year: 'numeric', 
                                        month: 'short', 
                                        day: 'numeric' 
                                    });
                                }
                                return '';
                            },
                            label: function(context) {
                                const value = context.parsed.y;
                                return `Close Price: $${value.toLocaleString(undefined, {
                                    minimumFractionDigits: 2,
                                    maximumFractionDigits: 2
                                })}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: getComputedStyle(document.documentElement).getPropertyValue('--bs-border-color') || '#dee2e6'
                        },
                        ticks: {
                            color: getComputedStyle(document.documentElement).getPropertyValue('--bs-body-color') || '#333',
                            callback: function(value, index) {
                                const label = this.getLabelForValue(value);
                                const allLabels = this.chart.data.labels;
                                
                                // Use smart date formatting if available
                                if (window.formatChartDateSmart) {
                                    return window.formatChartDateSmart(label, index, allLabels);
                                }
                                
                                // Fallback to simple date formatting
                                const date = new Date(label);
                                return date.toLocaleDateString(undefined, { 
                                    month: 'short', 
                                    day: 'numeric' 
                                });
                            }
                        }
                    },
                    y: {
                        grid: {
                            color: getComputedStyle(document.documentElement).getPropertyValue('--bs-border-color') || '#dee2e6'
                        },
                        ticks: {
                            color: getComputedStyle(document.documentElement).getPropertyValue('--bs-body-color') || '#333',
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }
    
    // Fetch price data for the given range
    function fetchPriceData(range) {
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
        
        // Show loading state
        const chartContainer = document.getElementById('priceChart').parentNode;
        chartContainer.classList.add('position-relative');
        
        // If there's an existing loading indicator, remove it
        const existingLoader = chartContainer.querySelector('.chart-loader');
        if (existingLoader) {
            existingLoader.remove();
        }
        
        // Add loading indicator
        const loader = document.createElement('div');
        loader.className = 'chart-loader position-absolute top-0 start-0 w-100 h-100 d-flex justify-content-center align-items-center bg-white bg-opacity-75';
        loader.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
        loader.style.zIndex = '1000';
        chartContainer.appendChild(loader);
        
        // Calculate date range
        const { startDate, endDate } = getDateRange(range);
        
        // Build URL with query parameters using the correct API endpoint
        let url = `/api/v1/stocks/${stockId}/price_history/?end_date=${endDate}`;
        if (startDate) {
            url += `&start_date=${startDate}`;
        }
        
        // Fetch data from API
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                // Remove loading indicator
                loader.remove();
                
                // Process the data for the chart
                const prices = data.results || data;
                if (prices && prices.length > 0) {
                    // Sort by date in ascending order
                    prices.sort((a, b) => new Date(a.date) - new Date(b.date));
                    
                    // Extract dates and close prices
                    const dates = prices.map(price => price.date);
                    const closePrices = prices.map(price => parseFloat(price.close_price));
                    
                    // Update chart data
                    chart.data.labels = dates;
                    chart.data.datasets[0].data = closePrices;
                    chart.update('none'); // No animation for better performance
                } else {
                    // Handle case when no price data is available
                    const noDataMsg = document.createElement('div');
                    noDataMsg.className = 'alert alert-info';
                    noDataMsg.textContent = 'No price history data available for this date range.';
                    
                    // Clear chart and show message
                    if (chart) {
                        chart.data.labels = [];
                        chart.data.datasets[0].data = [];
                        chart.update('none');
                    }
                    
                    // Only add message if not already present
                    if (!chartContainer.querySelector('.alert')) {
                        chartContainer.appendChild(noDataMsg);
                    }
                }
            })
            .catch(error => {
                // Remove loading indicator
                loader.remove();
                
                console.error('Error fetching price history:', error);
                
                // Show error message
                const errorMsg = document.createElement('div');
                errorMsg.className = 'alert alert-danger';
                errorMsg.textContent = 'Error loading price history data. Please try again later.';
                
                // Only add message if not already present
                if (!chartContainer.querySelector('.alert')) {
                    chartContainer.appendChild(errorMsg);
                }
            });
    }
    
    // Initialize the chart
    chart = initChart();
    
    // Add event listeners to date range buttons
    document.querySelectorAll('[data-range]').forEach(button => {
        button.addEventListener('click', function() {
            // Remove any existing alert messages
            const alerts = document.querySelectorAll('.alert');
            alerts.forEach(alert => alert.remove());
            
            const range = this.getAttribute('data-range');
            fetchPriceData(range);
        });
    });
    
    // Load initial data with 3-month range
    fetchPriceData('3M');
});
