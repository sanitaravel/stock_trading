'use strict';
{
    function setTheme(mode) {
        if (mode !== "light" && mode !== "dark" && mode !== "auto") {
            console.error(`Got invalid theme mode: ${mode}. Resetting to auto.`);
            mode = "auto";
        }
        document.documentElement.dataset.theme = mode;
        localStorage.setItem("theme", mode);
        
        // Update chart colors if any charts exist
        updateChartColors();

        if (mode === 'auto') {
            const systemDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
            document.documentElement.setAttribute('data-theme', systemDarkMode ? 'dark' : 'light');
            
            // Set the footer theme explicitly
            const footerTheme = systemDarkMode ? 'dark' : 'light';
            document.querySelectorAll('footer, .footer').forEach(el => {
                el.setAttribute('data-theme', footerTheme);
            });
        } else {
            document.documentElement.setAttribute('data-theme', mode);
            
            // Set the footer theme explicitly
            document.querySelectorAll('footer, .footer').forEach(el => {
                el.setAttribute('data-theme', mode);
            });
        }
    }

    function cycleTheme() {
        const currentTheme = localStorage.getItem("theme") || "auto";
        const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;

        if (prefersDark) {
            // Auto (dark) -> Light -> Dark
            if (currentTheme === "auto") {
                setTheme("light");
            } else if (currentTheme === "light") {
                setTheme("dark");
            } else {
                setTheme("auto");
            }
        } else {
            // Auto (light) -> Dark -> Light
            if (currentTheme === "auto") {
                setTheme("dark");
            } else if (currentTheme === "dark") {
                setTheme("light");
            } else {
                setTheme("auto");
            }
        }
    }

    function initTheme() {
        // Set theme defined in localStorage if there is one, or fallback to auto mode
        const currentTheme = localStorage.getItem("theme");
        currentTheme ? setTheme(currentTheme) : setTheme("auto");
    }
    
    function updateChartColors() {
        // If Chart.js is loaded, update all charts with new theme colors
        if (window.Chart && window.Chart.instances) {
            const isDark = document.documentElement.dataset.theme === 'dark' || 
                          (document.documentElement.dataset.theme === 'auto' && 
                           window.matchMedia('(prefers-color-scheme: dark)').matches);
            
            const gridColor = getComputedStyle(document.documentElement).getPropertyValue('--chart-grid').trim();
            const textColor = getComputedStyle(document.documentElement).getPropertyValue('--chart-text').trim();
            
            Object.values(Chart.instances).forEach(chart => {
                // Update grid lines
                if (chart.options.scales.x) {
                    chart.options.scales.x.grid.color = gridColor;
                    chart.options.scales.x.ticks.color = textColor;
                }
                if (chart.options.scales.y) {
                    chart.options.scales.y.grid.color = gridColor;
                    chart.options.scales.y.ticks.color = textColor;
                }
                
                // Update legend
                if (chart.options.plugins && chart.options.plugins.legend) {
                    chart.options.plugins.legend.labels.color = textColor;
                }
                
                chart.update();
            });
        }
    }

    // Listen for system preference changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
        if (document.documentElement.dataset.theme === 'auto') {
            updateChartColors();
        }
    });

    window.addEventListener('load', function() {
        const buttons = document.getElementsByClassName("theme-toggle");
        Array.from(buttons).forEach((btn) => {
            btn.addEventListener("click", cycleTheme);
        });
        
        // Update chart colors when the page loads
        updateChartColors();
    });

    // Initialize theme on script load
    initTheme();
}
