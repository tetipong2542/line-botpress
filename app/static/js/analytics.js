// Analytics Page JavaScript
// State
let currentMonth = new Date().getMonth(); // 0-11
let currentYear = new Date().getFullYear();
let charts = {}; // Store chart instances

// Thai month names
const thaiMonths = [
    'มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน',
    'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม'
];

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    updatePeriodDisplay();
    await loadAnalytics();
    setupPeriodNavigation();
});

// Load all analytics data
async function loadAnalytics() {
    const month = formatMonthParam();

    try {
        // Fetch all data in parallel
        const [summary, categoryData, trendsData] = await Promise.all([
            API.get(buildApiUrl(`analytics/summary?month=${month}`)),
            API.get(buildApiUrl(`analytics/by-category?month=${month}&type=expense`)),
            API.get(buildApiUrl(`analytics/trends?months=6`))
        ]);

        // Update UI
        updateSummaryCards(summary.summary);
        renderCategoryChart(categoryData.categories);
        renderTrendsChart(trendsData.trends);
        updateTopCategories(categoryData.categories);

    } catch (error) {
        console.error('Analytics load error:', error);
        showToast(error.message || 'ไม่สามารถโหลดข้อมูลได้', 'error');
    }
}

// Format month parameter (YYYY-MM)
function formatMonthParam() {
    const month = String(currentMonth + 1).padStart(2, '0');
    return `${currentYear}-${month}`;
}

// Update summary cards
function updateSummaryCards(summary) {
    // Income
    const incomeEl = document.querySelector('.summary-card.income .summary-amount');
    if (incomeEl) {
        incomeEl.textContent = `฿${summary.income.formatted.toLocaleString('th-TH', {minimumFractionDigits: 2})}`;
    }

    // Expense
    const expenseEl = document.querySelector('.summary-card.expense .summary-amount');
    if (expenseEl) {
        expenseEl.textContent = `฿${summary.expense.formatted.toLocaleString('th-TH', {minimumFractionDigits: 2})}`;
    }

    // Balance
    const balanceEl = document.querySelector('.summary-card.balance .summary-amount');
    if (balanceEl) {
        balanceEl.textContent = `฿${summary.balance.formatted.toLocaleString('th-TH', {minimumFractionDigits: 2})}`;
        // Update color based on positive/negative
        balanceEl.style.color = summary.balance.total >= 0 ? 'var(--success)' : 'var(--error)';
    }
}

// Render Vertical Bar Chart (Category Breakdown)
function renderCategoryChart(categories) {
    const canvas = document.getElementById('categoryChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    // Destroy existing chart
    if (charts.category) {
        charts.category.destroy();
    }

    if (categories.length === 0) {
        // Show empty state
        canvas.parentElement.innerHTML = `
            <div class="empty-state">
                <i data-lucide="bar-chart-2"></i>
                <p>ยังไม่มีข้อมูล</p>
            </div>
        `;
        lucide.createIcons();
        return;
    }

    // Prepare data
    const labels = categories.map(c => c.category_name);
    const amounts = categories.map(c => c.formatted);
    const colors = categories.map(c => c.category_color || '#ef4444');

    // Create chart
    charts.category = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'จำนวนเงิน (฿)',
                data: amounts,
                backgroundColor: colors,
                borderColor: colors,
                borderWidth: 1
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
                    callbacks: {
                        label: function(context) {
                            const cat = categories[context.dataIndex];
                            return [
                                `จำนวน: ฿${cat.formatted.toLocaleString('th-TH')}`,
                                `รายการ: ${cat.count} รายการ`,
                                `สัดส่วน: ${cat.percentage}%`
                            ];
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '฿' + value.toLocaleString('th-TH');
                        }
                    }
                }
            }
        }
    });
}

// Render Line Chart (Trends)
function renderTrendsChart(trends) {
    const canvas = document.getElementById('trendsChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    // Destroy existing chart
    if (charts.trends) {
        charts.trends.destroy();
    }

    if (trends.length === 0) {
        // Show empty state
        canvas.parentElement.innerHTML = `
            <div class="empty-state">
                <i data-lucide="trending-up"></i>
                <p>ยังไม่มีข้อมูล</p>
            </div>
        `;
        lucide.createIcons();
        return;
    }

    // Prepare data
    const labels = trends.map(t => t.month_label);
    const incomeData = trends.map(t => t.income / 100); // Convert to baht
    const expenseData = trends.map(t => t.expense / 100);

    // Create chart
    charts.trends = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'รายรับ',
                    data: incomeData,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'รายจ่าย',
                    data: expenseData,
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ฿' +
                                   context.parsed.y.toLocaleString('th-TH');
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '฿' + value.toLocaleString('th-TH');
                        }
                    }
                }
            }
        }
    });
}

// Update top categories list
function updateTopCategories(categories) {
    const container = document.getElementById('top-categories-list');
    if (!container) return;

    if (categories.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i data-lucide="inbox"></i>
                <p>ยังไม่มีข้อมูล</p>
            </div>
        `;
        lucide.createIcons();
        return;
    }

    // Render all categories (not just top 3)
    container.innerHTML = categories.map(cat => `
        <div class="category-stat-item">
            <div class="category-stat-header">
                <div class="category-stat-info">
                    <i data-lucide="${cat.category_icon}" style="color: ${cat.category_color}"></i>
                    <span class="category-stat-name">${cat.category_name}</span>
                </div>
                <div class="category-stat-amount">
                    <span class="amount">฿${cat.formatted.toLocaleString('th-TH')}</span>
                    <span class="percentage">${cat.percentage}%</span>
                </div>
            </div>
            <div class="category-stat-bar">
                <div class="category-stat-progress"
                     style="width: ${cat.percentage}%; background: ${cat.category_color}"></div>
            </div>
            ${cat.budget ? `
                <div class="category-stat-budget">
                    <span>งบ: ฿${cat.budget.formatted.toLocaleString('th-TH')}</span>
                    <span>เหลือ: ฿${(cat.budget.remaining / 100).toLocaleString('th-TH')}</span>
                    <span class="${cat.budget.usage_percentage > 100 ? 'over-budget' : ''}">
                        ${cat.budget.usage_percentage}%
                    </span>
                </div>
            ` : ''}
        </div>
    `).join('');

    lucide.createIcons();
}

// Period navigation
function setupPeriodNavigation() {
    const prevBtn = document.getElementById('prev-month');
    const nextBtn = document.getElementById('next-month');

    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            currentMonth--;
            if (currentMonth < 0) {
                currentMonth = 11;
                currentYear--;
            }
            updatePeriodDisplay();
            loadAnalytics();
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            currentMonth++;
            if (currentMonth > 11) {
                currentMonth = 0;
                currentYear++;
            }
            updatePeriodDisplay();
            loadAnalytics();
        });
    }
}

function updatePeriodDisplay() {
    const periodEl = document.getElementById('current-period');
    if (periodEl) {
        periodEl.textContent = `${thaiMonths[currentMonth]} ${currentYear + 543}`;
    }
}
