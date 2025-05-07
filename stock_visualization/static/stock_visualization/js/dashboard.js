document.addEventListener('DOMContentLoaded', function() {
    // Set up the portfolio comparison chart
    initPortfolioComparisonChart();
});

function initPortfolioComparisonChart() {
    const ctx = document.getElementById('portfolioComparisonChart').getContext('2d');
    
    // Show loading state
    const loadingText = new Chart(ctx, {
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
    
    // Fetch portfolio growth data from API
    fetch('/stock-visualization/api/portfolios/history/')
        .then(response => response.json())
        .then(data => {
            // Destroy loading chart
            loadingText.destroy();
            
            // Create the real chart
            new Chart(ctx, {
                type: 'line',
                data: data,
                options: {
                    responsive: true,
                    maintainAspectRatio: true, // Changed from false to true
                    aspectRatio: 2.5, // Add aspect ratio to control height/width ratio
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
        })
        .catch(error => {
            console.error('Error loading portfolio comparison data:', error);
            loadingText.destroy();
            
            // Show error state
            ctx.font = '16px Arial';
            ctx.fillStyle = 'red';
            ctx.textAlign = 'center';
            ctx.fillText('Error loading data. Please try again later.', ctx.canvas.width / 2, ctx.canvas.height / 2);
        });
}
