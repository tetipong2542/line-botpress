// Analytics Page JavaScript with Recurring Transactions Support
// State
let currentMonth = new Date().getMonth(); // 0-11
let currentYear = new Date().getFullYear();
let charts = {}; // Store chart instances
let recurringData = null; // Store recurring rules

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
    setupExportButton();
});

// Load all analytics data including recurring and loans
async function loadAnalytics() {
    const month = formatMonthParam();

    try {
        // Fetch all data in parallel (including loans)
        const [summary, categoryData, recurringRules, loansResponse] = await Promise.all([
            API.get(buildApiUrl(`analytics/summary?month=${month}`)),
            API.get(buildApiUrl(`analytics/by-category?month=${month}&type=expense`)),
            loadRecurringData(),
            API.get(buildApiUrl('loans'))
        ]);

        recurringData = recurringRules;
        const loans = loansResponse.loans || [];

        // Calculate recurring for current month
        const recurringMonthly = calculateMonthlyRecurring(recurringRules, currentMonth, currentYear);

        // Calculate loan payments for current month
        const loanMonthly = calculateMonthlyLoanPayments(loans, currentMonth, currentYear);

        // Update Simple Dashboard (Option 3)
        updateSimpleDashboard(summary.summary, recurringMonthly, loanMonthly);

        // Update charts and categories
        renderCategoryChart(categoryData.categories, recurringMonthly.expense_by_category);
        updateTopCategories(categoryData.categories, recurringMonthly.expense_by_category);

        // Load monthly payments section (recurring + loans)
        loadMonthlyPayments();

    } catch (error) {
        console.error('Analytics load error:', error);
        showToast(error.message || 'ไม่สามารถโหลดข้อมูลได้', 'error');
    }
}

// Load recurring rules
async function loadRecurringData() {
    try {
        const response = await API.get(buildApiUrl('recurring?active_only=true'));
        console.log('[Analytics] Recurring rules loaded:', response);
        // API returns {recurring_rules: [...]} not {recurring: [...]}
        return response.recurring_rules || [];
    } catch (error) {
        console.error('Recurring load error:', error);
        return [];
    }
}

// Calculate recurring forecast for a specific month
function calculateMonthlyRecurring(rules, month, year) {
    const startDate = new Date(year, month, 1);
    const endDate = new Date(year, month + 1, 0); // Last day of month

    console.log(`[Analytics] Calculating recurring for ${month + 1}/${year}`, {
        startDate: startDate.toISOString(),
        endDate: endDate.toISOString(),
        rulesCount: rules.length
    });

    let totalIncome = 0;
    let totalExpense = 0;
    const expenseByCategory = {}; // {category_id: {amount, name, icon, color}}
    const expensePayments = []; // Individual payment items for list display

    rules.forEach(rule => {
        // Start from rule's start_date, not next_run_date
        let currentDate = new Date(rule.start_date);

        // If start_date is after the target month, skip this rule
        if (currentDate > endDate) {
            return;
        }

        // Check if rule has end_date and it's before the target month
        let ruleEndDate = null;
        if (rule.end_date) {
            ruleEndDate = new Date(rule.end_date);
            if (ruleEndDate < startDate) {
                // Rule ended before this month, skip
                return;
            }
        }

        console.log(`[Analytics] Processing rule:`, {
            type: rule.type,
            amount: rule.amount / 100,
            freq: rule.freq,
            start_date: rule.start_date,
            end_date: rule.end_date || 'ไม่จำกัด',
            category: rule.category ? rule.category.name : 'N/A'
        });

        let occurrenceCount = 0;

        // Determine the actual end boundary (either month end or rule end_date)
        const actualEndDate = ruleEndDate && ruleEndDate < endDate ? ruleEndDate : endDate;

        // Generate occurrences from start_date up to actual end date
        while (currentDate <= actualEndDate && occurrenceCount < 100) { // Safety limit
            if (currentDate >= startDate && currentDate <= actualEndDate) {
                // This occurrence falls within the target month
                const amount = rule.amount / 100; // Convert satang to baht

                console.log(`  → Occurrence on ${currentDate.toISOString().split('T')[0]}: ฿${amount}`);

                if (rule.type === 'income') {
                    totalIncome += amount;
                } else {
                    totalExpense += amount;

                    // Add to expense payments list for display
                    expensePayments.push({
                        name: rule.category?.name_th || rule.category?.name || rule.note || 'รายจ่ายประจำ',
                        amount: amount,
                        date: new Date(currentDate),
                        type: 'recurring',
                        icon: rule.category?.icon || 'repeat',
                        color: rule.category?.color || '#8b5cf6',
                        category_id: rule.category_id,
                        isPaid: rule.is_paid_this_period || false
                    });

                    // Track by category
                    const catId = rule.category_id;
                    if (!expenseByCategory[catId]) {
                        expenseByCategory[catId] = {
                            category_id: catId,
                            category_name: rule.category ? rule.category.name : 'ไม่ระบุ',
                            category_icon: rule.category ? rule.category.icon : 'help-circle',
                            category_color: rule.category ? rule.category.color : '#6b7280',
                            amount: 0,
                            formatted: 0,
                            count: 0
                        };
                    }
                    expenseByCategory[catId].amount += amount;
                    expenseByCategory[catId].formatted += amount;
                    expenseByCategory[catId].count += 1;
                }

                occurrenceCount++;
            }

            // Calculate next occurrence
            currentDate = getNextOccurrence(currentDate, rule.freq, rule.day_of_week, rule.day_of_month);
        }
    });

    console.log('[Analytics] Recurring calculation result:', {
        totalIncome,
        totalExpense,
        categoryCount: Object.keys(expenseByCategory).length,
        expensePaymentsCount: expensePayments.length
    });

    return {
        income: totalIncome,
        expense: totalExpense,
        balance: totalIncome - totalExpense,
        expense_by_category: Object.values(expenseByCategory),
        expense_payments: expensePayments // Individual payment items for list display
    };
}

// Get next occurrence date for recurring rule
function getNextOccurrence(currentDate, freq, dayOfWeek, dayOfMonth) {
    const next = new Date(currentDate);

    if (freq === 'daily') {
        next.setDate(next.getDate() + 1);
    } else if (freq === 'weekly') {
        next.setDate(next.getDate() + 7);
    } else if (freq === 'monthly') {
        next.setMonth(next.getMonth() + 1);
        if (dayOfMonth) {
            const lastDay = new Date(next.getFullYear(), next.getMonth() + 1, 0).getDate();
            next.setDate(Math.min(dayOfMonth, lastDay));
        }
    } else if (freq === 'yearly') {
        next.setFullYear(next.getFullYear() + 1);
    }

    return next;
}

// Format month parameter (YYYY-MM)
function formatMonthParam() {
    const month = String(currentMonth + 1).padStart(2, '0');
    return `${currentYear}-${month}`;
}

// Update summary cards with regular + recurring breakdown
function updateSummaryCardsWithRecurring(summary, recurringMonthly) {
    // Regular income
    const regularIncome = summary.income.formatted;
    const recurringIncome = recurringMonthly.income;
    const totalIncome = regularIncome + recurringIncome;

    // Regular expense
    const regularExpense = summary.expense.formatted;
    const recurringExpense = recurringMonthly.expense;
    const totalExpense = regularExpense + recurringExpense;

    // Net balance
    const netBalance = totalIncome - totalExpense;

    // Update cards
    document.querySelector('.summary-card.regular-income .summary-amount').textContent =
        `฿${regularIncome.toLocaleString('th-TH', {minimumFractionDigits: 2})}`;

    document.querySelector('.summary-card.recurring-income .summary-amount').textContent =
        `฿${recurringIncome.toLocaleString('th-TH', {minimumFractionDigits: 2})}`;

    document.querySelector('.summary-card.total-income .summary-amount').textContent =
        `฿${totalIncome.toLocaleString('th-TH', {minimumFractionDigits: 2})}`;

    document.querySelector('.summary-card.regular-expense .summary-amount').textContent =
        `฿${regularExpense.toLocaleString('th-TH', {minimumFractionDigits: 2})}`;

    document.querySelector('.summary-card.recurring-expense .summary-amount').textContent =
        `฿${recurringExpense.toLocaleString('th-TH', {minimumFractionDigits: 2})}`;

    document.querySelector('.summary-card.total-expense .summary-amount').textContent =
        `฿${totalExpense.toLocaleString('th-TH', {minimumFractionDigits: 2})}`;

    const balanceCard = document.querySelector('.summary-card.net-balance');
    const balanceAmount = balanceCard.querySelector('.summary-amount');
    balanceAmount.textContent = `฿${netBalance.toLocaleString('th-TH', {minimumFractionDigits: 2})}`;

    // Update balance card styling
    balanceCard.classList.remove('positive', 'negative');
    if (netBalance >= 0) {
        balanceCard.classList.add('positive');
    } else {
        balanceCard.classList.add('negative');
    }
}

// Calculate loan payments for a specific month (works for any month, not just current)
function calculateMonthlyLoanPayments(loans, month, year) {
    let totalPayment = 0;
    let loanCount = 0;
    let totalInstallments = 0;
    let paidInstallments = 0;
    const payments = [];

    const targetDate = new Date(year, month, 1);

    loans.forEach(loan => {
        if (!loan.is_active) return;

        // Track overall progress
        totalInstallments += loan.term_months;
        paidInstallments += loan.paid_installments;

        // Calculate which installment falls in the target month
        const startDate = new Date(loan.start_date);
        
        // Calculate months difference from start_date to target month
        const monthsDiff = (year - startDate.getFullYear()) * 12 + (month - startDate.getMonth());
        
        // Installment number for target month (1-indexed)
        const installmentNumber = monthsDiff + 1;

        // Check if this installment is valid (between 1 and term_months)
        if (installmentNumber >= 1 && installmentNumber <= loan.term_months) {
            const amount = loan.monthly_payment / 100;
            totalPayment += amount;
            loanCount++;

            // Calculate payment date (same day as start_date, in target month)
            const paymentDay = startDate.getDate();
            const daysInMonth = new Date(year, month + 1, 0).getDate();
            const actualDay = Math.min(paymentDay, daysInMonth);
            const paymentDate = new Date(year, month, actualDay);

            payments.push({
                name: loan.name,
                amount: amount,
                date: paymentDate,
                installment: installmentNumber,
                totalInstallments: loan.term_months,
                isPaid: installmentNumber <= loan.paid_installments
            });
        }
    });

    return {
        totalPayment,
        loanCount,
        totalInstallments,
        paidInstallments,
        payments
    };
}

// Update Simple Dashboard (Option 3)
function updateSimpleDashboard(summary, recurringMonthly, loanMonthly) {
    // Calculate totals
    const regularIncome = summary.income.formatted || 0;
    const recurringIncome = recurringMonthly.income || 0;
    const totalIncome = regularIncome + recurringIncome;

    const regularExpense = summary.expense.formatted || 0;
    const recurringExpense = recurringMonthly.expense || 0;
    const loanExpense = loanMonthly.totalPayment || 0;
    const totalExpense = regularExpense + recurringExpense + loanExpense;

    const netBalance = totalIncome - totalExpense;

    // Format function
    const formatAmount = (amount) => '฿' + amount.toLocaleString('th-TH', { minimumFractionDigits: 0 });

    // Update Main 3 Cards
    document.getElementById('total-income').textContent = formatAmount(totalIncome);
    document.getElementById('total-expense').textContent = formatAmount(totalExpense);
    document.getElementById('net-balance').textContent = formatAmount(netBalance);

    // Update expense note
    const expenseNote = document.getElementById('expense-note');
    if (loanExpense > 0) {
        expenseNote.textContent = `(รวมสินเชื่อ ฿${loanExpense.toLocaleString()})`;
        expenseNote.style.display = 'block';
    } else {
        expenseNote.style.display = 'none';
    }

    // Update balance status
    const balanceCard = document.getElementById('balance-card');
    const balanceStatus = document.getElementById('balance-status');
    balanceCard.classList.remove('positive', 'negative');

    if (netBalance >= 0) {
        balanceCard.classList.add('positive');
        if (netBalance > totalIncome * 0.2) {
            balanceStatus.textContent = '💚 ดีมาก!';
        } else {
            balanceStatus.textContent = '💛 พอใช้';
        }
    } else {
        balanceCard.classList.add('negative');
        balanceStatus.textContent = '❌ ขาดทุน';
    }

    // Update Expense Breakdown
    const calcPercent = (amount) => totalExpense > 0 ? ((amount / totalExpense) * 100).toFixed(1) : 0;

    document.getElementById('expense-regular').textContent = formatAmount(regularExpense);
    document.getElementById('expense-regular-pct').textContent = `(${calcPercent(regularExpense)}%)`;

    document.getElementById('expense-recurring').textContent = formatAmount(recurringExpense);
    document.getElementById('expense-recurring-pct').textContent = `(${calcPercent(recurringExpense)}%)`;

    document.getElementById('expense-loan').textContent = formatAmount(loanExpense);
    document.getElementById('expense-loan-pct').textContent = `(${calcPercent(loanExpense)}%)`;

    // Update loan count badge and detail list
    const loanCount = document.getElementById('loan-count');
    const loanRow = document.getElementById('loan-row');
    
    if (loanMonthly.loanCount > 0) {
        loanCount.textContent = `${loanMonthly.loanCount} รายการ`;
        loanCount.style.display = 'inline-block';
        loanRow.style.display = 'flex';
        
        // Build loan detail list
        updateLoanDetailList(loanMonthly.payments, formatAmount);
    } else {
        loanCount.style.display = 'none';
        loanRow.style.display = 'none';
        document.getElementById('loan-detail-list').innerHTML = '';
    }

    document.getElementById('expense-total-detail').textContent = formatAmount(totalExpense);

    // Refresh icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

// Update Loan Detail List (for expandable section)
function updateLoanDetailList(loanPayments, formatAmount) {
    const container = document.getElementById('loan-detail-list');
    if (!container || !loanPayments || loanPayments.length === 0) return;

    // Calculate summary
    const paidLoans = loanPayments.filter(l => l.isPaid);
    const pendingLoans = loanPayments.filter(l => !l.isPaid);
    const paidAmount = paidLoans.reduce((sum, l) => sum + l.amount, 0);
    const pendingAmount = pendingLoans.reduce((sum, l) => sum + l.amount, 0);

    // Build loan items HTML
    const loanItemsHtml = loanPayments.map((loan, index) => {
        const isLast = index === loanPayments.length - 1;
        const isPaid = loan.isPaid;
        const badgeClass = isPaid ? 'paid' : 'pending';
        const badgeText = isPaid ? '<i data-lucide="check" class="inline-icon"></i> ชำระแล้ว' : `งวด ${loan.installment}/${loan.totalInstallments}`;
        const amountClass = isPaid ? 'paid' : '';
        
        return `
            <div class="loan-detail-item ${isLast ? 'last' : ''} ${isPaid ? 'is-paid' : ''}">
                <span class="loan-detail-connector">${isLast ? '└─' : '├─'}</span>
                <span class="loan-detail-name ${isPaid ? 'paid' : ''}">${loan.name}</span>
                <span class="loan-detail-amount ${amountClass}">${formatAmount(loan.amount)}</span>
                <span class="loan-detail-badge ${badgeClass}">${badgeText}</span>
            </div>
        `;
    }).join('');

    // Build summary HTML with Lucide icons
    const summaryHtml = `
        <div class="loan-summary-divider"></div>
        <div class="loan-summary-row">
            <span class="loan-summary-label"><i data-lucide="check-circle" class="inline-icon paid"></i> ชำระแล้ว (${paidLoans.length})</span>
            <span class="loan-summary-amount paid">${formatAmount(paidAmount)}</span>
        </div>
        <div class="loan-summary-row">
            <span class="loan-summary-label"><i data-lucide="clock" class="inline-icon pending"></i> คงเหลือ (${pendingLoans.length})</span>
            <span class="loan-summary-amount pending">${formatAmount(pendingAmount)}</span>
        </div>
    `;

    container.innerHTML = loanItemsHtml + summaryHtml;
    
    // Default open and refresh icons
    container.style.display = 'block';
    const expandIcon = document.getElementById('loan-expand-icon');
    if (expandIcon) expandIcon.style.transform = 'rotate(180deg)';
    
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

// Toggle Loan Detail visibility
function toggleLoanDetail() {
    const detailList = document.getElementById('loan-detail-list');
    const expandIcon = document.getElementById('loan-expand-icon');
    
    if (detailList.style.display === 'none') {
        detailList.style.display = 'block';
        expandIcon.style.transform = 'rotate(180deg)';
    } else {
        detailList.style.display = 'none';
        expandIcon.style.transform = 'rotate(0deg)';
    }
}

// Render Stacked Bar Chart (Category Breakdown: Regular + Recurring)
function renderCategoryChart(regularCategories, recurringCategories) {
    const canvas = document.getElementById('categoryChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    // Destroy existing chart
    if (charts.category) {
        charts.category.destroy();
    }

    // Merge regular and recurring categories
    const categoryMap = {};

    // Add regular categories
    regularCategories.forEach(cat => {
        categoryMap[cat.category_id] = {
            id: cat.category_id,
            name: cat.category_name,
            icon: cat.category_icon,
            color: cat.category_color,
            regular: cat.formatted,
            recurring: 0
        };
    });

    // Add recurring categories
    recurringCategories.forEach(cat => {
        if (categoryMap[cat.category_id]) {
            categoryMap[cat.category_id].recurring = cat.formatted;
        } else {
            categoryMap[cat.category_id] = {
                id: cat.category_id,
                name: cat.category_name,
                icon: cat.category_icon,
                color: cat.category_color,
                regular: 0,
                recurring: cat.formatted
            };
        }
    });

    const categories = Object.values(categoryMap);

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
    const labels = categories.map(c => c.name);
    const regularData = categories.map(c => c.regular);
    const recurringData = categories.map(c => c.recurring);

    // Create stacked chart
    charts.category = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'ปกติ',
                    data: regularData,
                    backgroundColor: '#3b82f6',
                    borderColor: '#3b82f6',
                    borderWidth: 1
                },
                {
                    label: 'ประจำ',
                    data: recurringData,
                    backgroundColor: '#8b5cf6',
                    borderColor: '#8b5cf6',
                    borderWidth: 1
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
                        footer: function(context) {
                            const index = context[0].dataIndex;
                            const regular = regularData[index];
                            const recurring = recurringData[index];
                            const total = regular + recurring;
                            return `รวม: ฿${total.toLocaleString('th-TH', {minimumFractionDigits: 2})}`;
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

// Render Stacked Line Chart (Trends: Regular + Recurring)
function renderTrendsChart(trends, recurringRules) {
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

    // Calculate recurring for each month in trends
    const labels = trends.map(t => t.month_label);
    const regularIncomeData = trends.map(t => t.income / 100);
    const regularExpenseData = trends.map(t => t.expense / 100);

    // Calculate recurring for each month
    const recurringIncomeData = [];
    const recurringExpenseData = [];

    trends.forEach(trend => {
        // Parse month from trend (format: "Jan 2026" -> month: 0, year: 2026)
        const [monthName, yearStr] = trend.month_label.split(' ');
        const monthIndex = thaiMonths.indexOf(monthName);
        const year = parseInt(yearStr) - 543; // Convert BE to AD

        const recurringMonthly = calculateMonthlyRecurring(recurringRules, monthIndex, year);
        recurringIncomeData.push(recurringMonthly.income);
        recurringExpenseData.push(recurringMonthly.expense);
    });

    // Create stacked chart
    charts.trends = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'รายรับ (ปกติ)',
                    data: regularIncomeData,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    fill: true,
                    stack: 'income'
                },
                {
                    label: 'รายรับ (ประจำ)',
                    data: recurringIncomeData,
                    borderColor: '#8b5cf6',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    tension: 0.4,
                    fill: true,
                    stack: 'income'
                },
                {
                    label: 'รายจ่าย (ปกติ)',
                    data: regularExpenseData,
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.4,
                    fill: true,
                    stack: 'expense'
                },
                {
                    label: 'รายจ่าย (ประจำ)',
                    data: recurringExpenseData,
                    borderColor: '#ec4899',
                    backgroundColor: 'rgba(236, 72, 153, 0.1)',
                    tension: 0.4,
                    fill: true,
                    stack: 'expense'
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
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ฿' +
                                   context.parsed.y.toLocaleString('th-TH', {minimumFractionDigits: 2});
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

// Update top categories list with regular + recurring
function updateTopCategories(regularCategories, recurringCategories) {
    const container = document.getElementById('top-categories-list');
    if (!container) return;

    // Merge regular and recurring
    const categoryMap = {};

    regularCategories.forEach(cat => {
        categoryMap[cat.category_id] = {
            id: cat.category_id,
            name: cat.category_name,
            icon: cat.category_icon,
            color: cat.category_color,
            regular: cat.formatted,
            recurring: 0,
            total: cat.formatted,
            budget: cat.budget,
            count: cat.count
        };
    });

    recurringCategories.forEach(cat => {
        if (categoryMap[cat.category_id]) {
            categoryMap[cat.category_id].recurring = cat.formatted;
            categoryMap[cat.category_id].total += cat.formatted;
            categoryMap[cat.category_id].count += cat.count;
        } else {
            categoryMap[cat.category_id] = {
                id: cat.category_id,
                name: cat.category_name,
                icon: cat.category_icon,
                color: cat.category_color,
                regular: 0,
                recurring: cat.formatted,
                total: cat.formatted,
                budget: null,
                count: cat.count
            };
        }
    });

    const categories = Object.values(categoryMap);

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

    // Sort by total amount
    categories.sort((a, b) => b.total - a.total);

    // Calculate percentage
    const totalAmount = categories.reduce((sum, cat) => sum + cat.total, 0);
    categories.forEach(cat => {
        cat.percentage = totalAmount > 0 ? ((cat.total / totalAmount) * 100).toFixed(1) : 0;
    });

    // Render all categories with enhanced card layout
    container.innerHTML = categories.map(cat => `
        <div class="category-card-enhanced">
            <div class="category-card-header">
                <div class="category-icon-circle" style="background: ${cat.color}20; color: ${cat.color};">
                    <i data-lucide="${cat.icon}"></i>
                </div>
                <div class="category-info">
                    <span class="category-name">${cat.name}</span>
                    <div class="category-amounts-row">
                        <span class="category-total">฿${cat.total.toLocaleString('th-TH')}</span>
                        <span class="category-percentage-badge" style="background: ${cat.color}15; color: ${cat.color};">${cat.percentage}%</span>
                    </div>
                </div>
            </div>
            <div class="category-breakdown-tags">
                <span class="tag regular">
                    <i data-lucide="circle" class="tag-icon"></i>
                    ปกติ ฿${cat.regular.toLocaleString('th-TH')}
                </span>
                <span class="tag recurring">
                    <i data-lucide="repeat" class="tag-icon"></i>
                    ประจำ ฿${cat.recurring.toLocaleString('th-TH')}
                </span>
            </div>
            <div class="category-progress-bar">
                <div class="category-progress-fill" style="width: ${cat.percentage}%; background: ${cat.color};"></div>
            </div>
            ${cat.budget ? `
                <div class="category-budget-info ${cat.budget.usage_percentage > 100 ? 'over-budget' : ''}">
                    <span>งบ ฿${cat.budget.formatted.toLocaleString('th-TH')}</span>
                    <span>เหลือ ฿${((cat.budget.remaining || 0) / 100).toLocaleString('th-TH')}</span>
                    <span class="usage">${cat.budget.usage_percentage}%</span>
                </div>
            ` : ''}
        </div>
    `).join('');

    lucide.createIcons();
}

// Period navigation with Touch Swipe Support
function setupPeriodNavigation() {
    const prevBtn = document.getElementById('prev-period');
    const nextBtn = document.getElementById('next-period');
    const periodSelector = document.querySelector('.period-selector');
    const container = document.querySelector('.mobile-container');

    // Helper: Trigger haptic feedback
    function triggerHaptic() {
        if ('vibrate' in navigator) {
            navigator.vibrate(15);
        }
    }
    
    // Previous period
    function goToPrevPeriod() {
        triggerHaptic();
        currentMonth--;
        if (currentMonth < 0) {
            currentMonth = 11;
            currentYear--;
        }
        animatePeriodChange('left');
        updatePeriodDisplay();
        loadAnalytics();
    }
    
    // Next period
    function goToNextPeriod() {
        triggerHaptic();
        currentMonth++;
        if (currentMonth > 11) {
            currentMonth = 0;
            currentYear++;
        }
        animatePeriodChange('right');
        updatePeriodDisplay();
        loadAnalytics();
    }
    
    // Animate period change
    function animatePeriodChange(direction) {
        const periodEl = document.getElementById('current-period');
        if (!periodEl) return;
        
        periodEl.style.transition = 'none';
        periodEl.style.transform = direction === 'left' ? 'translateX(30px)' : 'translateX(-30px)';
        periodEl.style.opacity = '0';
        
        requestAnimationFrame(() => {
            periodEl.style.transition = 'all 0.3s ease';
            periodEl.style.transform = 'translateX(0)';
            periodEl.style.opacity = '1';
        });
    }

    if (prevBtn) {
        prevBtn.addEventListener('click', goToPrevPeriod);
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', goToNextPeriod);
    }
    
    // ===== SWIPE GESTURE DETECTION (Improved - entire header area) =====
    const swipeArea = document.querySelector('.page-header') || periodSelector;
    if (swipeArea) {
        let touchStartX = 0;
        let touchStartY = 0;
        let touchStartTime = 0;
        let isSwiping = false;
        
        swipeArea.addEventListener('touchstart', (e) => {
            touchStartX = e.touches[0].clientX;
            touchStartY = e.touches[0].clientY;
            touchStartTime = Date.now();
            isSwiping = true;
        }, { passive: true });
        
        swipeArea.addEventListener('touchmove', (e) => {
            if (!isSwiping) return;
            const deltaX = e.touches[0].clientX - touchStartX;
            
            // Visual feedback during swipe
            if (periodSelector && Math.abs(deltaX) > 20) {
                periodSelector.style.transform = `translateX(${deltaX * 0.3}px)`;
                periodSelector.style.transition = 'none';
            }
        }, { passive: true });
        
        swipeArea.addEventListener('touchend', (e) => {
            if (!isSwiping) return;
            
            const touchEndX = e.changedTouches[0].clientX;
            const touchEndY = e.changedTouches[0].clientY;
            const deltaX = touchEndX - touchStartX;
            const deltaY = touchEndY - touchStartY;
            const deltaTime = Date.now() - touchStartTime;
            
            // Reset visual feedback
            if (periodSelector) {
                periodSelector.style.transition = 'transform 0.3s ease';
                periodSelector.style.transform = '';
            }
            
            // Check if it's a horizontal swipe (more horizontal than vertical, lower threshold)
            if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 30 && deltaTime < 600) {
                if (deltaX > 0) {
                    // Swipe right -> go to previous month
                    goToPrevPeriod();
                } else {
                    // Swipe left -> go to next month
                    goToNextPeriod();
                }
            }
            
            isSwiping = false;
        }, { passive: true });
    }
    
    // ===== PULL-TO-REFRESH =====
    if (container) {
        let pullStartY = 0;
        let isPulling = false;
        let pullIndicator = null;
        
        // Create pull indicator
        function createPullIndicator() {
            pullIndicator = document.createElement('div');
            pullIndicator.className = 'pull-to-refresh-indicator';
            pullIndicator.innerHTML = `
                <i data-lucide="arrow-down"></i>
                <span>ดึงลงเพื่อรีเฟรช</span>
            `;
            pullIndicator.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                height: 60px;
                background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                font-weight: 600;
                transform: translateY(-100%);
                transition: transform 0.3s ease;
                z-index: 9998;
            `;
            document.body.appendChild(pullIndicator);
            lucide.createIcons();
        }
        
        createPullIndicator();
        
        container.addEventListener('touchstart', (e) => {
            if (container.scrollTop === 0) {
                pullStartY = e.touches[0].clientY;
                isPulling = true;
            }
        }, { passive: true });
        
        container.addEventListener('touchmove', (e) => {
            if (!isPulling) return;
            
            const pullY = e.touches[0].clientY;
            const pullDistance = pullY - pullStartY;
            
            if (pullDistance > 0 && pullDistance < 150) {
                const progress = Math.min(pullDistance / 100, 1);
                pullIndicator.style.transform = `translateY(${progress * 60 - 60}px)`;
                
                if (pullDistance > 80) {
                    pullIndicator.innerHTML = `
                        <i data-lucide="loader" class="spinning"></i>
                        <span>ปล่อยเพื่อรีเฟรช</span>
                    `;
                    lucide.createIcons();
                }
            }
        }, { passive: true });
        
        container.addEventListener('touchend', async () => {
            if (!isPulling) return;
            
            const pullY = parseFloat(pullIndicator.style.transform.replace(/[^0-9.-]/g, '')) || 0;
            
            if (pullY >= 0) {
                // Trigger refresh
                triggerHaptic();
                pullIndicator.innerHTML = `
                    <i data-lucide="loader" class="spinning"></i>
                    <span>กำลังโหลด...</span>
                `;
                lucide.createIcons();
                
                await loadAnalytics();
                showToast('รีเฟรชข้อมูลสำเร็จ', 'success');
            }
            
            // Hide indicator
            pullIndicator.style.transform = 'translateY(-100%)';
            setTimeout(() => {
                pullIndicator.innerHTML = `
                    <i data-lucide="arrow-down"></i>
                    <span>ดึงลงเพื่อรีเฟรช</span>
                `;
                lucide.createIcons();
            }, 300);
            
            isPulling = false;
        }, { passive: true });
    }
}

function updatePeriodDisplay() {
    const periodEl = document.getElementById('current-period');
    if (periodEl) {
        periodEl.textContent = `${thaiMonths[currentMonth]} ${currentYear + 543}`;
    }
}

// ===== EXPORT TO CSV =====
function setupExportButton() {
    const exportBtn = document.getElementById('btn-export');
    if (!exportBtn) return;

    exportBtn.addEventListener('click', async () => {
        try {
            // Show loading
            const originalContent = exportBtn.innerHTML;
            exportBtn.disabled = true;
            exportBtn.innerHTML = '<i data-lucide="loader" class="spinning"></i><span>กำลัง Export...</span>';
            lucide.createIcons();

            // Get current month range
            const month = formatMonthParam();
            const [year, monthNum] = month.split('-');

            // Calculate start and end dates
            const startDate = `${year}-${monthNum}-01`;
            const lastDay = new Date(parseInt(year), parseInt(monthNum), 0).getDate();
            const endDate = `${year}-${monthNum}-${lastDay}`;

            // Build export URL
            const exportUrl = buildApiUrl(`export/transactions`) +
                            `?start_date=${startDate}&end_date=${endDate}`;

            // Download file
            window.location.href = exportUrl;

            // Reset button after short delay
            setTimeout(() => {
                exportBtn.disabled = false;
                exportBtn.innerHTML = originalContent;
                lucide.createIcons();
            }, 1000);

            showToast('กำลัง Download ไฟล์...', 'success');

        } catch (error) {
            console.error('Export error:', error);
            showToast('ไม่สามารถ Export ได้', 'error');

            exportBtn.disabled = false;
            exportBtn.innerHTML = originalContent;
            lucide.createIcons();
        }
    });
}

// ===== MONTHLY PAYMENTS SECTION =====
async function loadMonthlyPayments() {
    const listContainer = document.getElementById('monthly-payment-list');
    if (!listContainer) return;

    try {
        // Fetch recurring rules and loans
        const [recurringResponse, loansResponse] = await Promise.all([
            API.get(buildApiUrl('recurring?active_only=true')),
            API.get(buildApiUrl('loans'))
        ]);

        const recurringRules = recurringResponse.recurring_rules || [];
        const loans = loansResponse.loans || [];

        // Calculate recurring expense for current month
        const recurringMonthly = calculateMonthlyRecurring(recurringRules, currentMonth, currentYear);
        const recurringExpense = recurringMonthly.expense;

        // Calculate loan payments for selected month (using start_date-based calculation)
        let loanPayments = [];

        loans.forEach(loan => {
            if (!loan.is_active) return;

            const startDate = new Date(loan.start_date);
            const monthsDiff = (currentYear - startDate.getFullYear()) * 12 + (currentMonth - startDate.getMonth());
            const installmentNumber = monthsDiff + 1;

            // Check if this installment is valid (between 1 and term_months)
            if (installmentNumber >= 1 && installmentNumber <= loan.term_months) {
                const amount = loan.monthly_payment / 100;
                
                // Calculate payment date
                const paymentDay = startDate.getDate();
                const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
                const actualDay = Math.min(paymentDay, daysInMonth);
                const paymentDate = new Date(currentYear, currentMonth, actualDay);

                loanPayments.push({
                    name: loan.name,
                    amount: amount,
                    date: paymentDate,
                    type: 'loan',
                    installment: `งวดที่ ${installmentNumber}/${loan.term_months}`,
                    isPaid: installmentNumber <= loan.paid_installments
                });
            }
        });

        // Note: Summary cards were removed from HTML (now using Simple Dashboard)
        // The data is already displayed in updateSimpleDashboard()

        // Build payment list - use expense_payments from calculateMonthlyRecurring for consistency
        const allPayments = [];

        // Add recurring expenses from calculated data (consistent with Simple Dashboard)
        if (recurringMonthly.expense_payments) {
            recurringMonthly.expense_payments.forEach(payment => {
                allPayments.push(payment);
            });
        }

        // Add loan payments
        loanPayments.forEach(loan => {
            allPayments.push({
                ...loan,
                icon: 'landmark',
                color: '#ef4444'
            });
        });

        // Sort by date
        allPayments.sort((a, b) => a.date - b.date);

        // Render list
        if (allPayments.length === 0) {
            listContainer.innerHTML = `
                <div class="empty-state" style="padding: 24px;">
                    <i data-lucide="check-circle"></i>
                    <p>ไม่มีรายการต้องจ่ายเดือนนี้</p>
                </div>
            `;
        } else {
            listContainer.innerHTML = allPayments.map(payment => {
                const day = payment.date.getDate();
                const month = payment.date.toLocaleDateString('th-TH', { month: 'short' });
                const typeClass = payment.type === 'loan' ? 'loan' : 'recurring';
                const isPaid = payment.isPaid || false;
                const paidClass = isPaid ? 'paid' : 'pending';
                
                // Badge and label based on type and status
                let typeLabel, badgeHtml;
                if (payment.type === 'loan') {
                    if (isPaid) {
                        typeLabel = '✓ ชำระแล้ว';
                        badgeHtml = `<span class="payment-badge paid">ชำระแล้ว</span>`;
                    } else {
                        typeLabel = payment.installment;
                        badgeHtml = '';
                    }
                } else {
                    typeLabel = 'ประจำ';
                    badgeHtml = isPaid ? `<span class="payment-badge paid">ชำระแล้ว</span>` : '';
                }

                return `
                    <div class="payment-item ${typeClass} ${paidClass}">
                        <div class="payment-item-date">
                            <span class="payment-day">${day}</span>
                            <span class="payment-month">${month}</span>
                        </div>
                        <div class="payment-item-icon" style="background: ${payment.color}20; color: ${payment.color}">
                            <i data-lucide="${payment.icon}"></i>
                        </div>
                        <div class="payment-item-info">
                            <span class="payment-name">${payment.name}</span>
                            <span class="payment-type">${typeLabel}</span>
                        </div>
                        <div class="payment-item-right">
                            ${badgeHtml}
                            <span class="payment-item-amount ${isPaid ? 'paid' : ''}">฿${payment.amount.toLocaleString('th-TH')}</span>
                        </div>
                    </div>
                `;
            }).join('');
        }

        lucide.createIcons();

    } catch (error) {
        console.error('Load monthly payments error:', error);
        listContainer.innerHTML = `
            <div class="empty-state" style="padding: 24px;">
                <i data-lucide="alert-circle"></i>
                <p>ไม่สามารถโหลดข้อมูลได้</p>
            </div>
        `;
        lucide.createIcons();
    }
}

