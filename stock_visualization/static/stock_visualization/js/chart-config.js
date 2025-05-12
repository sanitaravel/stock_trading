// Global Chart.js configuration for theme support
document.addEventListener('DOMContentLoaded', function() {
    if (window.Chart) {
        // Add default configuration for all charts
        Chart.defaults.color = getComputedStyle(document.documentElement).getPropertyValue('--chart-text').trim();
        Chart.defaults.scale.grid.color = getComputedStyle(document.documentElement).getPropertyValue('--chart-grid').trim();
        Chart.defaults.plugins.title.color = getComputedStyle(document.documentElement).getPropertyValue('--chart-text').trim();

        // Set plugin defaults for better title and legend readability
        Chart.defaults.plugins.title.font = {
            size: 14,
            weight: 'bold',
            family: "'Open Sans', 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif"
        };

        // Set default chart title to not display
        Chart.defaults.plugins.title.display = false;
        
        // Add global tooltip title callback for date formatting
        Chart.defaults.plugins.tooltip.callbacks.title = function(tooltipItems) {
            if (tooltipItems.length > 0) {
                const dateStr = tooltipItems[0].label;
                // Check if this is a date format (YYYY-MM-DD)
                if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
                    const date = new Date(dateStr);
                    return date.toLocaleDateString(undefined, { 
                        weekday: 'short', 
                        year: 'numeric', 
                        month: 'short', 
                        day: 'numeric' 
                    });
                }
            }
            return tooltipItems[0]?.label || '';
        };
        
        // Global date formatter function that can be used across charts
        window.formatChartDate = function(dateStr, format = 'short') {
            if (!dateStr) return '';
            const date = new Date(dateStr);
            
            switch(format) {
                case 'full':
                    return date.toLocaleDateString(undefined, { 
                        weekday: 'long',
                        year: 'numeric', 
                        month: 'long', 
                        day: 'numeric' 
                    });
                case 'medium':
                    return date.toLocaleDateString(undefined, { 
                        year: 'numeric', 
                        month: 'short', 
                        day: 'numeric' 
                    });
                case 'monthYear':
                    return date.toLocaleDateString(undefined, { 
                        year: '2-digit', 
                        month: 'short'
                    });
                case 'short':
                default:
                    return date.toLocaleDateString(undefined, { 
                        month: 'short', 
                        day: 'numeric' 
                    });
            }
        };
        
        // Function to create charts with theme awareness
        window.createThemeAwareChart = function(ctx, config) {
            // Add class to parent for theme awareness
            if (ctx.canvas) {
                ctx.canvas.parentNode.classList.add('chart-override-js');
            }
            
            // Ensure config has proper theme-based colors
            if (!config.options) config.options = {};
            if (!config.options.scales) config.options.scales = {};
            
            // Add x and y scales if not present
            ['x', 'y'].forEach(scale => {
                if (!config.options.scales[scale]) config.options.scales[scale] = {};
                if (!config.options.scales[scale].grid) config.options.scales[scale].grid = {};
                if (!config.options.scales[scale].ticks) config.options.scales[scale].ticks = {};
                
                config.options.scales[scale].grid.color = getComputedStyle(document.documentElement)
                    .getPropertyValue('--chart-grid').trim();
                config.options.scales[scale].ticks.color = getComputedStyle(document.documentElement)
                    .getPropertyValue('--chart-text').trim();
            });
            
            // Apply date formatting to x-axis if it contains dates
            if (config.data && config.data.labels && config.data.labels.length > 0) {
                const firstLabel = config.data.labels[0];
                // Check if labels are dates in ISO format
                if (typeof firstLabel === 'string' && /^\d{4}-\d{2}-\d{2}/.test(firstLabel)) {
                    if (!config.options.scales.x.ticks.callback) {
                        config.options.scales.x.ticks.callback = function(value, index) {
                            const label = this.getLabelForValue(value);
                            return window.formatChartDate(label, 
                                config.data.labels.length > 30 ? 'monthYear' : 'short');
                        };
                    }
                }
            }
            
            // Add legend configuration
            if (!config.options.plugins) config.options.plugins = {};
            if (!config.options.plugins.legend) config.options.plugins.legend = {};
            if (!config.options.plugins.legend.labels) config.options.plugins.legend.labels = {};
            
            config.options.plugins.legend.labels.color = getComputedStyle(document.documentElement)
                .getPropertyValue('--chart-text').trim();
            
            return new Chart(ctx, config);
        };

        // Add to the Chart creation wrapper
        const originalChart = Chart.constructor;
        Chart.constructor = function(ctx, config) {
            if (!config.options) config.options = {};
            if (!config.options.plugins) config.options.plugins = {};
            if (!config.options.plugins.title) config.options.plugins.title = {};
            
            // Force title to not display by default
            config.options.plugins.title.display = false;

            // Ensure chart titles in cards with blue headers have proper contrast
            if (config.options && config.options.plugins && config.options.plugins.title) {
                // Check if this chart is in a card with a blue header
                const canvas = ctx.canvas;
                const card = canvas.closest('.card');
                if (card && card.querySelector('.card-header.bg-primary')) {
                    config.options.plugins.title.color = getComputedStyle(document.documentElement)
                        .getPropertyValue('--body-color').trim();
                } else {
                    // Default title color
                    config.options.plugins.title.color = getComputedStyle(document.documentElement)
                        .getPropertyValue('--chart-text').trim();
                }
            }
            
            return new originalChart(ctx, config);
        };
    }
});
