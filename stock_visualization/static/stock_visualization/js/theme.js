'use strict';
{
    function setTheme(mode) {
        if (mode !== "light" && mode !== "dark") {
            console.error(`Got invalid theme mode: ${mode}. Resetting to light.`);
            mode = "light";
        }
        document.documentElement.dataset.theme = mode;
        localStorage.setItem("theme", mode);

        // Update chart colors if any charts exist
        updateChartColors();

        document.documentElement.setAttribute('data-theme', mode);

        // Set the footer theme explicitly
        document.querySelectorAll('footer, .footer').forEach(el => {
            el.setAttribute('data-theme', mode);
        });
    } function cycleTheme() {
        const currentTheme = localStorage.getItem("theme") || "light";

        // Simple toggle between light and dark
        if (currentTheme === "light") {
            setTheme("dark");
        } else {
            setTheme("light");
        }
    } function initTheme() {
        // Set theme defined in localStorage if there is one, or fallback to light mode
        const currentTheme = localStorage.getItem("theme");
        currentTheme ? setTheme(currentTheme) : setTheme("light");
    }
    function updateChartColors() {
        // If Chart.js is loaded, update all charts with new theme colors
        if (window.Chart && window.Chart.instances) {
            const isDark = document.documentElement.dataset.theme === 'dark';

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
    } window.addEventListener('load', function () {
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
