document.addEventListener('DOMContentLoaded', () => {
    if (typeof Chart === 'undefined' || !window.dashboardData) return;
    initStatusChart();
    initEvolutionChart();
});

function initStatusChart() {
    const canvas = document.getElementById('statusChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const data = window.dashboardData.chartStatus;

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Simulação', 'Cotação', 'Envio'],
            datasets: [{
                data: [
                    data.simulacao || 0,
                    data.cotacao || 0,
                    data.envio || 0
                ],
                backgroundColor: ['#FF8C00', '#3B82F6', '#10B981'],
                borderWidth: 0,
                hoverOffset: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#1a1a1a',
                    padding: 12,
                    cornerRadius: 8,
                    titleFont: {
                        size: 13,
                        weight: '600'
                    },
                    bodyFont: {
                        size: 14,
                        weight: '700'
                    },
                    callbacks: {
                        label: function (context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            },
            cutout: '65%'
        }
    });
}

function initEvolutionChart() {
    const canvas = document.getElementById('evolutionChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const data = window.dashboardData.chartEvolution;

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.dates || [],
            datasets: [{
                label: 'Propostas',
                data: data.counts || [],
                borderColor: '#FF8C00',
                backgroundColor: 'rgba(255, 140, 0, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointHoverRadius: 6,
                pointBackgroundColor: '#FF8C00',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointHoverBackgroundColor: '#FF8C00',
                pointHoverBorderColor: '#fff',
                pointHoverBorderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#1a1a1a',
                    padding: 12,
                    cornerRadius: 8,
                    titleFont: {
                        size: 13,
                        weight: '600'
                    },
                    bodyFont: {
                        size: 14,
                        weight: '700'
                    },
                    callbacks: {
                        label: function (context) {
                            return `Propostas: ${context.parsed.y}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1,
                        color: '#6b7280',
                        font: {
                            size: 12,
                            weight: '500'
                        }
                    },
                    grid: {
                        color: '#e5e7eb',
                        drawBorder: false
                    }
                },
                x: {
                    ticks: {
                        color: '#6b7280',
                        font: {
                            size: 12,
                            weight: '500'
                        }
                    },
                    grid: {
                        display: false,
                        drawBorder: false
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
