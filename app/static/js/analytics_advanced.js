// Advanced Analytics JavaScript
// State
let charts = {};
let currentPeriod = 30; // Default 30 days
let customStartDate = null;
let customEndDate = null;

// Thai day names
const thaiDays = ['อา.', 'จ.', 'อ.', 'พ.', 'พฤ.', 'ศ.', 'ส.'];

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    setupPeriodSelector();
    setupCustomDateRange();
    setupRefreshButton();
    await loadAdvancedAnalytics();
});

// Load all advanced analytics data
async function loadAdvancedAnalytics() {
    try {
        const [financialHealth, dailyAverages, velocity, savingsRate,
                categoryGrowth, heatmap, scatter, forecast,
                savingsGoals] = await Promise.all([
            API.get(buildApiUrl(`analytics/financial-health?months=3`)),
            API.get(buildApiUrl(`analytics/daily-averages?days=${currentPeriod}`)),
            API.get(buildApiUrl(`analytics/spending-velocity?days=${currentPeriod}`)),
            API.get(buildApiUrl(`analytics/savings-rate?months=6`)),
            API.get(buildApiUrl(`analytics/category-growth?months=6`)),
            API.get(buildApiUrl(`analytics/heatmap?days=${currentPeriod}`)),
            API.get(buildApiUrl(`analytics/scatter?days=${currentPeriod}`)),
            API.get(buildApiUrl(`predictions/forecast?days=30`)),
            API.get(buildApiUrl('savings-goals'))
        ]);

        // Update UI
        updateFinancialHealth(financialHealth);
        updateDailyAverages(dailyAverages);
        updateVelocity(velocity);
        updateSavingsRate(savingsRate);
        updateCategoryGrowth(categoryGrowth);
        renderHeatmap(heatmap);
        renderScatter(scatter);
        renderForecast(forecast);
        updateSavingsGoals(savingsGoals.goals);

    } catch (error) {
        console.error('Analytics load error:', error);
        showToast(error.message || 'ไม่สามารถโหลดข้อมูลได้', 'error');
    }
}

// Period selector
function setupPeriodSelector() {
    const periodSelect = document.getElementById('period-type');
    if (periodSelect) {
        periodSelect.addEventListener('change', (e) => {
            const value = e.target.value;
            const customRange = document.getElementById('custom-date-range');

            if (value === 'custom') {
                customRange.classList.remove('hidden');
            } else {
                customRange.classList.add('hidden');
                currentPeriod = parseInt(value);
                loadAdvancedAnalytics();
            }
        });
    }
}

// Custom date range
function setupCustomDateRange() {
    const applyBtn = document.getElementById('btn-apply-range');
    if (applyBtn) {
        applyBtn.addEventListener('click', async () => {
            const startDate = document.getElementById('start-date').value;
            const endDate = document.getElementById('end-date').value;

            if (!startDate || !endDate) {
                showToast('กรุณาระบุวันที่เริ่มและวันที่สิ้นสุด', 'error');
                return;
            }

            customStartDate = startDate;
            customEndDate = endDate;
            loadAdvancedAnalytics();
            showToast('ใช้ช่วงเวลาเรียบร้อยแล้ว', 'success');
        });
    }
}

// Refresh button
function setupRefreshButton() {
    const refreshBtn = document.getElementById('btn-refresh');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            loadAdvancedAnalytics();
            showToast('รีเฟรชข้อมูลเรียบร้อยแล้ว', 'success');
        });
    }
}

// Update financial health score
function updateFinancialHealth(data) {
    const scoreValue = document.getElementById('score-value');
    const scoreGrade = document.getElementById('score-grade');
    const scoreProgress = document.getElementById('score-progress');
    const scoreFactors = document.getElementById('score-factors');
    const scoreRecommendations = document.getElementById('score-recommendations');

    if (!data || !data.score) return;

    // Update score
    scoreValue.textContent = data.score;
    scoreGrade.textContent = data.grade;

    // Update progress circle
    const circumference = 283; // 2 * PI * 45
    const offset = circumference - (data.score / 100 * circumference);
    scoreProgress.style.strokeDashoffset = offset;

    // Set color based on score
    if (data.score >= 80) {
        scoreProgress.style.stroke = '#10b981'; // Green
    } else if (data.score >= 60) {
        scoreProgress.style.stroke = '#f59e0b'; // Yellow
    } else {
        scoreProgress.style.stroke = '#ef4444'; // Red
    }

    // Update factors
    const factorLabels = {
        budget_adherence: 'การควบคุมงบประมาณ',
        savings_consistency: 'ความสม่ำเสมอในการออมเงิน',
        spending_stability: 'ความเสถียรของการใช้จ่าย',
        income_diversity: 'ความหลากหลายของรายได้'
    };

    let factorsHtml = '';
    for (const [key, factor] of Object.entries(data.factors)) {
        const percentage = factor.score;
        factorsHtml += `
            <div class="factor-item">
                <div class="factor-name">${factorLabels[key]}</div>
                <div class="factor-bar">
                    <div class="factor-progress" style="width: ${percentage}%; background: ${getColorForScore(percentage)}"></div>
                </div>
                <div style="text-align: right; margin-top: 0.25rem; font-size: 0.875rem;">
                    ${percentage}%
                </div>
            </div>
        `;
    }
    scoreFactors.innerHTML = factorsHtml;

    // Update recommendations
    if (data.recommendations && data.recommendations.length > 0) {
        let recsHtml = '';
        for (const rec of data.recommendations) {
            recsHtml += `
                <div class="recommendation-item">
                    <i data-lucide="alert-triangle"></i>
                    <span>${rec}</span>
                </div>
            `;
        }
        scoreRecommendations.innerHTML = recsHtml;
    }

    lucide.createIcons();
}

// Update daily averages
function updateDailyAverages(data) {
    if (!data || !data.daily_averages) return;

    const avgIncome = document.getElementById('avg-income');
    const avgExpense = document.getElementById('avg-expense');
    const avgNet = document.getElementById('avg-net');
    const weekdayWeekend = document.getElementById('weekday-weekend');

    const da = data.daily_averages;
    avgIncome.textContent = `฿${da.income_avg_formatted.toLocaleString('th-TH', {minimumFractionDigits: 2})}`;
    avgExpense.textContent = `฿${da.expense_avg_formatted.toLocaleString('th-TH', {minimumFractionDigits: 2})}`;
    avgNet.textContent = `฿${da.net_avg_formatted.toLocaleString('th-TH', {minimumFractionDigits: 2})}`;

    // Update weekday vs weekend
    if (data.weekday_vs_weekend) {
        const wv = data.weekday_vs_weekend;
        weekdayWeekend.innerHTML = `
            <div class="comparison-item">
                <div class="comparison-label">วันธรรม์</div>
                <div class="comparison-value">฿${wv.weekday_avg_formatted.toLocaleString('th-TH', {minimumFractionDigits: 2})}</div>
            </div>
            <div class="comparison-item">
                <div class="comparison-label">วันหยุด</div>
                <div class="comparison-value">฿${wv.weekend_avg_formatted.toLocaleString('th-TH', {minimumFractionDigits: 2})}</div>
            </div>
        `;
    }
}

// Update velocity
function updateVelocity(data) {
    if (!data || !data.velocity) return;

    const velDaily = document.getElementById('velocity-daily');
    const velWeekly = document.getElementById('velocity-weekly');
    const velMonthly = document.getElementById('velocity-monthly');
    const velTrend = document.getElementById('velocity-trend');
    const velForecast = document.getElementById('velocity-forecast');

    const v = data.velocity;
    velDaily.textContent = `฿${v.daily_rate_formatted.toLocaleString('th-TH', {minimumFractionDigits: 2})}`;
    velWeekly.textContent = `฿${v.weekly_rate_formatted.toLocaleString('th-TH', {minimumFractionDigits: 2})}`;
    velMonthly.textContent = `฿${v.monthly_rate_formatted.toLocaleString('th-TH', {minimumFractionDigits: 2})}`;

    // Update trend
    const acc = data.acceleration;
    let trendIcon = 'minus';
    let trendText = 'คงที่';
    let trendColor = 'var(--text-muted)';

    if (acc.trend === 'speeding_up') {
        trendIcon = 'trending-up';
        trendText = 'เพิ่มขึ้น';
        trendColor = 'var(--error)';
    } else if (acc.trend === 'slowing_down') {
        trendIcon = 'trending-down';
        trendText = 'ลดลง';
        trendColor = 'var(--success)';
    }

    velTrend.innerHTML = `
        <div style="display: flex; align-items: center; gap: 0.5rem; color: ${trendColor};">
            <i data-lucide="${trendIcon}"></i>
            <span>${trendText}</span>
        </div>
    `;

    // Update forecast
    if (data.forecast) {
        const f = data.forecast;
        velForecast.innerHTML = `
            <div class="forecast-item">
                <div class="forecast-label">คาดการณ์ 7 วัน</div>
                <div class="forecast-value">฿${f.next_7_days_formatted.toLocaleString('th-TH', {minimumFractionDigits: 2})}</div>
            </div>
            <div class="forecast-item">
                <div class="forecast-label">คาดการณ์ 30 วัน</div>
                <div class="forecast-value">฿${f.next_30_days_formatted.toLocaleString('th-TH', {minimumFractionDigits: 2})}</div>
            </div>
        `;
    }

    lucide.createIcons();
}

// Update savings rate
function updateSavingsRate(data) {
    if (!data || !data.savings_rate) return;

    const savingsRate = document.getElementById('savings-rate');
    const savingsTrend = document.getElementById('savings-trend');

    const sr = data.savings_rate;
    savingsRate.textContent = `${sr.overall_rate}%`;

    // Update trend
    const comp = data.comparison;
    if (comp) {
        let trendIcon = 'minus';
        let trendText = 'คงที่';
        let trendColor = 'var(--text-muted)';

        if (comp.trend === 'improving') {
            trendIcon = 'trending-up';
            trendText = 'ดีขึ้น';
            trendColor = 'var(--success)';
        } else if (comp.trend === 'declining') {
            trendIcon = 'trending-down';
            trendText = 'แย่ลง';
            trendColor = 'var(--error)';
        }

        savingsTrend.innerHTML = `
            <div style="display: flex; align-items: center; gap: 0.5rem; color: ${trendColor};">
                <i data-lucide="${trendIcon}"></i>
                <span>${trendText} ${comp.vs_previous_period > 0 ? '+' : ''}${comp.vs_previous_period}%</span>
            </div>
        `;
    }

    // Render savings rate chart
    renderSavingsRateChart(sr.monthly_rates);

    lucide.createIcons();
}

// Render savings rate chart
function renderSavingsRateChart(monthlyRates) {
    const canvas = document.getElementById('savingsRateChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    if (charts.savingsRate) {
        charts.savingsRate.destroy();
    }

    if (!monthlyRates || monthlyRates.length === 0) {
        canvas.parentElement.innerHTML = `
            <div class="empty-state">
                <i data-lucide="piggy-bank"></i>
                <p>ยังไม่มีข้อมูล</p>
            </div>
        `;
        lucide.createIcons();
        return;
    }

    charts.savingsRate = new Chart(ctx, {
        type: 'line',
        data: {
            labels: monthlyRates.map(m => m.month),
            datasets: [{
                label: 'อัตราการออมเงิน (%)',
                data: monthlyRates.map(m => m.rate),
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    }
});

// Update category growth
function updateCategoryGrowth(data) {
    if (!data || !data.categories) return;

    const container = document.getElementById('category-growth');
    if (!container) return;

    if (data.categories.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i data-lucide="line-chart"></i>
                <p>ยังไม่มีข้อมูล</p>
            </div>
        `;
        lucide.createIcons();
        return;
    }

    container.innerHTML = data.categories.map(cat => {
        let trendIcon = 'minus';
        let trendClass = 'stable';
        let trendText = 'คงที่';

        if (cat.trend === 'up') {
            trendIcon = 'trending-up';
            trendClass = 'up';
            trendText = 'เพิ่มขึ้น';
        } else if (cat.trend === 'down') {
            trendIcon = 'trending-down';
            trendClass = 'down';
            trendText = 'ลดลง';
        }

        return `
            <div class="growth-item">
                <div class="growth-header">
                    <div class="growth-category">
                        <i data-lucide="${cat.category_icon}" style="color: ${cat.category_color}"></i>
                        <span class="growth-name">${cat.category_name}</span>
                    </div>
                    <div class="growth-trend ${trendClass}">
                        <i data-lucide="${trendIcon}"></i>
                        <span>${trendText} ${cat.growth_rate > 0 ? '+' : ''}${cat.growth_rate}%</span>
                    </div>
                </div>
                <div class="growth-bar">
                    <div class="growth-progress"
                         style="width: ${Math.min(100, Math.abs(cat.growth_rate))}%; background: ${cat.category_color}"></div>
                </div>
            </div>
        `;
    }).join('');

    lucide.createIcons();
}

// Render heatmap
function renderHeatmap(data) {
    const canvas = document.getElementById('heatmapChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    if (charts.heatmap) {
        charts.heatmap.destroy();
    }

    if (!data || !data.heatmap || data.heatmap.length === 0) {
        canvas.parentElement.innerHTML = `
            <div class="empty-state">
                <i data-lucide="grid"></i>
                <p>ยังไม่มีข้อมูล</p>
            </div>
        `;
        lucide.createIcons();
        return;
    }

    // Prepare heatmap data (7 days x 24 hours)
    const heatmapData = Array(7).fill(null).map(() => Array(24).fill(0));
    const maxTotal = data.max_total || 1;

    for (const item of data.heatmap) {
        const day = item.day_of_week; // 0 = Sunday
        const hour = item.hour;
        if (day >= 0 && day < 7 && hour >= 0 && hour < 24) {
            heatmapData[day][hour] = item.total;
        }
    }

    // Create color function
    const getColor = (value) => {
        const intensity = value / maxTotal;
        if (intensity < 0.33) return '#10b981'; // Green
        if (intensity < 0.66) return '#f59e0b'; // Yellow
        return '#ef4444'; // Red
    };

    // Create dataset
    const datasets = [];
    for (let day = 0; day < 7; day++) {
        datasets.push({
            label: thaiDays[day],
            data: heatmapData[day],
            backgroundColor: heatmapData[day].map(getColor),
            borderColor: 'transparent',
            borderWidth: 0
        });
    }

    charts.heatmap = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Array.from({length: 24}, (_, i) => `${i}:00`),
            datasets: datasets
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
                            const value = context.parsed.y;
                            return `฿${(value / 100).toLocaleString('th-TH', {minimumFractionDigits: 2})}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    stacked: true
                },
                y: {
                    stacked: true,
                    beginAtZero: true
                }
            }
        }
    }
});

// Render scatter plot
function renderScatter(data) {
    const canvas = document.getElementById('scatterChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    if (charts.scatter) {
        charts.scatter.destroy();
    }

    if (!data || !data.scatter || data.scatter.length === 0) {
        canvas.parentElement.innerHTML = `
            <div class="empty-state">
                <i data-lucide="scatter"></i>
                <p>ยังไม่มีข้อมูล</p>
            </div>
        `;
        lucide.createIcons();
        return;
    }

    charts.scatter = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'หมวดหมู่',
                data: data.scatter.map(s => ({
                    x: s.count,
                    y: s.avg_amount / 100, // Convert satang to baht
                    category: s
                })),
                backgroundColor: data.scatter.map(s => s.category_color),
                pointRadius: 8,
                pointHoverRadius: 12
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
                            const point = context.raw;
                            const cat = point.category;
                            return [
                                `${cat.category_name}`,
                                `จำนวน: ${cat.count} รายการ`,
                                `เฉลี่ยง: ฿${(cat.avg_amount / 100).toLocaleString('th-TH', {minimumFractionDigits: 2})}`,
                                `รวม: ฿${(cat.amount / 100).toLocaleString('th-TH', {minimumFractionDigits: 2})}`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'จำนวนรายการ'
                    },
                    beginAtZero: true
                },
                y: {
                    title: {
                        display: true,
                        text: 'จำนวนเงินเฉลี่ยง (บาท)'
                    },
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '฿' + value.toLocaleString('th-TH');
                        }
                    }
                }
            }
        }
    }
});

// Render forecast chart
function renderForecast(data) {
    const canvas = document.getElementById('forecastChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    if (charts.forecast) {
        charts.forecast.destroy();
    }

    if (!data || !data.forecast || data.forecast.length === 0) {
        canvas.parentElement.innerHTML = `
            <div class="empty-state">
                <i data-lucide="trending-up"></i>
                <p>ยังไม่มีข้อมูล</p>
            </div>
        `;
        lucide.createIcons();
        return;
    }

    const forecast = data.forecast;
    const labels = forecast.map(f => f.date);
    const predictedData = forecast.map(f => f.predicted / 100); // Convert to baht
    const lowerBound = forecast.map(f => f.lower_bound / 100);
    const upperBound = forecast.map(f => f.upper_bound / 100);

    charts.forecast = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'คาดการณ์',
                    data: predictedData,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4,
                    fill: false
                },
                {
                    label: 'ช่วงความเชื่อมั่น',
                    data: lowerBound,
                    borderColor: 'rgba(59, 130, 246, 0.3)',
                    backgroundColor: 'transparent',
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0
                },
                {
                    label: 'ช่วงความเชื่อมั่น',
                    data: upperBound,
                    borderColor: 'rgba(59, 130, 246, 0.3)',
                    backgroundColor: 'transparent',
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0
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
                            const value = context.parsed.y;
                            return `฿${value.toLocaleString('th-TH', {minimumFractionDigits: 2})}`;
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
    }
});

// Update forecast summary
if (data && data.summary) {
    const summaryEl = document.getElementById('forecast-summary');
    if (summaryEl) {
        const s = data.summary;
        summaryEl.innerHTML = `
            <div class="forecast-item">
                <div class="forecast-label">คาดการณ์รวม</div>
                <div class="forecast-value">฿${s.total_predicted_formatted.toLocaleString('th-TH', {minimumFractionDigits: 2})}</div>
            </div>
            <div class="forecast-item">
                <div class="forecast-label">ค่าเฉลี่ยงต่อวัน</div>
                <div class="forecast-value">฿${s.daily_average_formatted.toLocaleString('th-TH', {minimumFractionDigits: 2})}</div>
            </div>
            <div class="forecast-item">
                <div class="forecast-label">ความเชื่อมั่น</div>
                <div class="forecast-value">${(s.confidence * 100).toFixed(0)}%</div>
            </div>
        `;
    }
}

// Update savings goals
function updateSavingsGoals(goals) {
    const container = document.getElementById('savings-goals');
    if (!container) return;

    if (!goals || goals.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i data-lucide="target"></i>
                <p>ยังไม่มีเป้าหมายการออมเงิน</p>
                <button class="btn-primary" onclick="showAddGoalModal()">เพิ่มเป้าหมาย</button>
            </div>
        `;
        lucide.createIcons();
        return;
    }

    container.innerHTML = goals.map(goal => {
        let statusClass = 'on-track';
        let statusText = 'ตามแผน';

        if (goal.is_completed) {
            statusClass = 'completed';
            statusText = 'บรรลุโลภแล้ว';
        } else if (goal.is_overdue) {
            statusClass = 'off-track';
            statusText = 'เลยกำหนด';
        } else if (!goal.on_track) {
            statusClass = 'off-track';
            statusText = 'ไม่ตามแผน';
        }

        return `
            <div class="goal-item">
                <div class="goal-header">
                    <div class="goal-name">${goal.name}</div>
                    <div class="goal-status ${statusClass}">${statusText}</div>
                </div>
                <div class="goal-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${Math.min(100, goal.progress)}%"></div>
                    </div>
                    <div style="text-align: center; margin-top: 0.5rem; font-size: 0.875rem;">
                        ${goal.progress.toFixed(1)}%
                    </div>
                </div>
                <div class="goal-details">
                    <div class="goal-detail">
                        <div class="detail-label">เป้าหมาย</div>
                        <div class="detail-value">฿${goal.target_formatted.toLocaleString('th-TH')}</div>
                    </div>
                    <div class="goal-detail">
                        <div class="detail-label">ปัจจุบัน</div>
                        <div class="detail-value">฿${goal.current_formatted.toLocaleString('th-TH')}</div>
                    </div>
                    <div class="goal-detail">
                        <div class="detail-label">เหลือ</div>
                        <div class="detail-value">฿${((goal.target - goal.current) / 100).toLocaleString('th-TH', {minimumFractionDigits: 2})}</div>
                    </div>
                    <div class="goal-detail">
                        <div class="detail-label">วันที่เหลือ</div>
                        <div class="detail-value">${goal.days_remaining} วัน</div>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    lucide.createIcons();
}

// Helper function to get color for score
function getColorForScore(score) {
    if (score >= 80) return '#10b981'; // Green
    if (score >= 60) return '#f59e0b'; // Yellow
    return '#ef4444'; // Red
}

// Show add goal modal (placeholder)
function showAddGoalModal() {
    showToast('ฟีเจอร์เพิ่มเป้าหมายจะเพิ่มในภายหลัง', 'info');
}

// Build API URL
function buildApiUrl(endpoint) {
    return `/api/v1/projects/${window.PROJECT_ID}/${endpoint}`;
}
