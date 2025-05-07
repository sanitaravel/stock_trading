document.addEventListener('DOMContentLoaded', function() {
    // Initialize all charts
    initPortfolioHistoryChart();
    initAllocationChart();
    initPositionPerformanceChart();
});

function initPortfolioHistoryChart() {
    const ctx = document.getElementById('portfolioHistoryChart').getContext('2d');
    
    // Show loading state
    const loadingChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Loading...'],
            datasets: [{
                label: 'Loading data...',
                data: [0],
                backgroundColor: '#f8f9fa'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
    
    // Fetch portfolio history data from API
    fetch(`/stock-visualization/api/portfolio/${portfolioId}/history/`)
        .then(response => response.json())
        .then(data => {
            // Destroy loading chart
            loadingChart.destroy();
            
            // Create the real chart
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Portfolio Value',
                        data: data.values,
                        backgroundColor: 'rgba(78, 115, 223, 0.05)',
                        borderColor: 'rgba(78, 115, 223, 1)',
                        pointBackgroundColor: 'rgba(78, 115, 223, 1)',
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: 'rgba(78, 115, 223, 1)',
                        borderWidth: 2,
                        pointRadius: 3,
                        lineTension: 0.3,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true, // Changed from false to true
                    aspectRatio: 2.5, // Add aspect ratio to control height/width ratio
                    plugins: {
                        tooltip: {
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
                            grid: {
                                display: false
                            }
                        },
                        y: {
                            ticks: {
                                callback: function(value) {
                                    return '$' + value.toLocaleString();
                                }
                            }
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error loading portfolio history data:', error);
            loadingChart.destroy();
            
            // Show error message
            ctx.font = '16px Arial';
            ctx.fillStyle = 'red';
            ctx.textAlign = 'center';
            ctx.fillText('Error loading data. Please try again later.', ctx.canvas.width / 2, ctx.canvas.height / 2);
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
            maintainAspectRatio: false,
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
            maintainAspectRatio: false,
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
