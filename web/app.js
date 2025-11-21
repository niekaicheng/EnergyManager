// Energy Manager Web Application
// Frontend JavaScript for Energy Manager

// Configuration
const API_BASE = window.location.origin;

// State management
let currentPage = 'dashboard';
let goalsCache = [];
let eventsCache = [];

// Chart instances
let energyChartInstance = null;
let balanceChartInstance = null;

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    initializeNavigation();
    initializeDatePickers();
    initializeApp();
});

// Navigation
function initializeNavigation() {
    console.log('[Navigation] Initializing...');
    const navItems = document.querySelectorAll('.nav-item');
    console.log(`[Navigation] Found ${navItems.length} nav items`);
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            if (item.dataset.page) {
                console.log('[Navigation] Clicked:', item.dataset.page);
                e.preventDefault();
                const page = item.dataset.page;
                navigateToPage(page);
            }
        });
    });
}

function navigateToPage(page) {
    console.log('[Navigation] Navigating to:', page);
    // Update navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    const activeNav = document.querySelector(`[data-page="${page}"]`);
    if (activeNav) {
        activeNav.classList.add('active');
    } else {
        console.error(`[Navigation] Nav item for ${page} not found`);
    }

    // Update page content
    document.querySelectorAll('.page').forEach(p => {
        p.classList.remove('active');
    });
    document.getElementById(`${page}-page`).classList.add('active');

    currentPage = page;

    // Load page-specific data
    loadPageData(page);
}

async function loadPageData(page) {
    switch (page) {
        case 'dashboard':
            await loadDashboard();
            break;
        case 'goals':
            await loadGoals();
            break;
        case 'journal':
            await loadJournal(90);
            break;
        case 'trends':
            await loadTrends(14);
            break;
        case 'health':
            await loadHealthMetrics();
            break;
        case 'plan':
            await loadPlan();
            break;
    }
}

// Initialize app
async function initializeApp() {
    await loadDashboard();
}

// ==================== DASHBOARD ====================
async function loadDashboard() {
    try {
        const todayEvents = await fetchTodayEvents();
        const goals = await fetchGoals();
        goalsCache = goals; // Update cache for modals
        const healthData = await fetchTodayHealth();

        updateDashboardStats(todayEvents, goals, healthData);
        updateEnergyChart(7);
        updateBalanceChart(7);
        updateRecentActivity(todayEvents);
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

function updateDashboardStats(events, goals, health) {
    // Safety check for health object
    health = health || {};

    // Energy Balance
    const energyBalance = events.reduce((sum, e) => sum + (e.energy_cost || 0), 0);
    const balanceEl = document.getElementById('energy-balance');
    if (balanceEl) {
        balanceEl.textContent = `${energyBalance > 0 ? '+' : ''}${energyBalance}`;
        balanceEl.style.color = energyBalance >= 0 ? 'var(--success)' : 'var(--error)';
    }

    // Total time logged
    const totalMinutes = events.reduce((sum, e) => sum + (e.duration_minutes || 0), 0);
    const timeEl = document.getElementById('time-logged');
    if (timeEl) {
        timeEl.textContent = `${(totalMinutes / 60).toFixed(1)}h`;
    }
    const eventsEl = document.getElementById('time-events');
    if (eventsEl && eventsEl.querySelector('span')) {
        eventsEl.querySelector('span').textContent = `${events.length} events`;
    }

    // Active goals
    const activeGoals = goals.filter(g => g.is_active).length;
    const goalsEl = document.getElementById('active-goals');
    if (goalsEl) {
        goalsEl.textContent = activeGoals;
    }

    // Sleep score
    const sleepScore = health.sleep_score || 0;
    const sleepScoreEl = document.getElementById('sleep-score');
    if (sleepScoreEl) {
        sleepScoreEl.textContent = sleepScore || '--';
        if (sleepScore >= 75) {
            sleepScoreEl.style.color = 'var(--success)';
        } else if (sleepScore >= 60) {
            sleepScoreEl.style.color = 'var(--warning)';
        } else if (sleepScore > 0) {
            sleepScoreEl.style.color = 'var(--error)';
        }
    }

    const sleepHours = (health.sleep_total_min || 0) / 60;
    const sleepDurEl = document.getElementById('sleep-duration');
    if (sleepDurEl && sleepDurEl.querySelector('span')) {
        sleepDurEl.querySelector('span').textContent = sleepHours > 0 ? `${sleepHours.toFixed(1)} hours` : '--';
    }
}

function updateRecentActivity(events) {
    const container = document.getElementById('recent-activity');

    if (events.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No events logged today</p></div>';
        return;
    }

    container.innerHTML = events.slice(0, 5).map(event => `
        <div class="activity-item">
            <div class="activity-time">${formatTime(event.timestamp_start)}</div>
            <div class="activity-state ${event.key_state.toLowerCase().replace(' ', '-')}">${event.key_state}</div>
            <div class="activity-details">
                <div class="activity-name">${event.activity}</div>
                <div class="activity-meta">
                    ${event.duration_minutes} minutes
                    ${event.goal_name ? `• ${event.goal_name}` : ''}
                </div>
            </div>
            ${event.energy_cost ? `
                <div class="activity-cost ${event.energy_cost >= 0 ? 'positive' : 'negative'}">
                    ${event.energy_cost >= 0 ? '+' : ''}${event.energy_cost}
                </div>
            ` : ''}
        </div>
    `).join('');
}

// ==================== GOALS MANAGEMENT ====================
async function loadGoals() {
    try {
        const goals = await fetchGoals();
        goalsCache = goals;
        displayGoals(goals);
    } catch (error) {
        console.error('Error loading goals:', error);
    }
}

function displayGoals(goals) {
    const container = document.getElementById('goals-list');

    if (goals.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="12" y1="8" x2="12" y2="12"/>
                    <line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                <h4>No goals yet</h4>
                <p>Create your first goal to get started</p>
            </div>
        `;
        return;
    }

    // Create list header
    let html = `
        <div class="goal-list-header">
            <div class="col-name">Goal Name</div>
            <div class="col-priority">Priority</div>
            <div class="col-cost">Energy Cost</div>
            <div class="col-stats">Stats</div>
            <div class="col-actions">Actions</div>
        </div>
    `;

    html += goals.map(goal => `
        <div class="goal-list-item">
            <div class="col-name">
                <div class="goal-title">${goal.goal_name}</div>
            </div>
            <div class="col-priority">
                <span class="goal-priority-badge p${goal.priority_level}">P${goal.priority_level}</span>
            </div>
            <div class="col-cost">
                <span class="goal-cost-value ${goal.energy_cost >= 0 ? 'positive' : 'negative'}">
                    ${goal.energy_cost >= 0 ? '+' : ''}${goal.energy_cost}
                </span>
            </div>
            <div class="col-stats">
                <span class="stat-item" title="Total Events">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <polyline points="12 6 12 12 16 14"></polyline>
                    </svg>
                    ${goal.event_count || 0}
                </span>
                <span class="stat-item" title="Total Hours">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <polyline points="12 6 12 12 16 14"></polyline>
                    </svg>
                    ${goal.total_hours?.toFixed(1) || '0.0'}h
                </span>
            </div>
            <div class="col-actions">
                <button class="btn-icon" onclick="editGoal(${goal.goal_id})" title="Edit">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                    </svg>
                </button>
                <button class="btn-icon danger" onclick="archiveGoal(${goal.goal_id})" title="Archive">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                </button>
            </div>
        </div>
    `).join('');

    container.innerHTML = html;
}

function showAddGoalModal() {
    document.getElementById('add-goal-modal').classList.add('active');
}

async function addGoal(event) {
    event.preventDefault();

    const goalData = {
        goal_name: document.getElementById('goal-name').value,
        priority_level: parseInt(document.getElementById('goal-priority').value),
        energy_cost: parseInt(document.getElementById('goal-cost').value)
    };

    try {
        await createGoal(goalData);
        closeModal('add-goal-modal');
        document.getElementById('add-goal-form').reset();
        await loadGoals();
        showNotification('Goal added successfully!', 'success');
    } catch (error) {
        showNotification('Error adding goal: ' + error.message, 'error');
    }
}

function editGoal(goalId) {
    const goal = goalsCache.find(g => g.goal_id === goalId);
    if (!goal) return;

    // Populate modal with current goal data
    document.getElementById('goal-name').value = goal.goal_name;
    document.getElementById('goal-priority').value = goal.priority_level;
    document.getElementById('goal-cost').value = goal.energy_cost;

    // Change modal title
    const modal = document.getElementById('add-goal-modal');
    const modalTitle = modal.querySelector('h3');
    modalTitle.textContent = 'Edit Goal';

    // Change form submit to update instead of add
    const form = document.getElementById('add-goal-form');
    form.onsubmit = async (e) => {
        e.preventDefault();

        const goalData = {
            goal_name: document.getElementById('goal-name').value,
            priority_level: parseInt(document.getElementById('goal-priority').value),
            energy_cost: parseInt(document.getElementById('goal-cost').value)
        };

        try {
            await updateGoal(goalId, goalData);
            closeModal('add-goal-modal');
            form.reset();
            modalTitle.textContent = 'Add New Goal';
            form.onsubmit = addGoal; // Reset to add function
            await loadGoals();
            showNotification('Goal updated successfully!', 'success');
        } catch (error) {
            showNotification('Error updating goal: ' + error.message, 'error');
        }
    };

    modal.classList.add('active');
}

async function archiveGoal(goalId) {
    if (!confirm('Are you sure you want to archive this goal?')) return;

    try {
        await archiveGoalById(goalId);
        await loadGoals();
        showNotification('Goal archived successfully!', 'success');
    } catch (error) {
        showNotification('Error archiving goal: ' + error.message, 'error');
    }
}

// ==================== JOURNAL ====================
async function loadJournal(days = 90) {
    if (typeof renderJournal === 'function') {
        await renderJournal(days);
    } else {
        console.error('renderJournal function not found. Is calendar.js loaded?');
    }
}



// ==================== TRENDS ====================
async function loadTrends(days) {
    try {
        const trends = await fetchTrends(days);
        displayTrends(trends);
        updateTrendsCharts(trends);
    } catch (error) {
        console.error('Error loading trends:', error);
    }
}

function displayTrends(trends) {
    const container = document.getElementById('trend-table');

    if (trends.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No trend data available</p></div>';
        return;
    }

    container.innerHTML = `
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Sleep Score</th>
                        <th>RHR</th>
                        <th>Stress</th>
                        <th>Steps</th>
                        <th>Events</th>
                        <th>Total Time</th>
                        <th>Energy Net</th>
                    </tr>
                </thead>
                <tbody>
                    ${trends.map(day => {
        const sleepColor = (day.sleep_score >= 75) ? 'var(--success)' : (day.sleep_score >= 60) ? 'var(--warning)' : 'var(--error)';
        return `
                        <tr>
                            <td><strong>${formatDate(day.date)}</strong></td>
                            <td style="color: ${day.sleep_score ? sleepColor : 'var(--text-secondary)'}">
                                ${day.sleep_score || '-'}
                            </td>
                            <td>${day.rhr_avg || '-'}</td>
                            <td>${day.stress_avg || '-'}</td>
                            <td>${day.steps_total || '-'}</td>
                            <td>${day.event_count || 0}</td>
                            <td>${day.total_hours?.toFixed(1) || '0.0'}h</td>
                            <td style="color: ${(day.energy_net || 0) >= 0 ? 'var(--success)' : 'var(--error)'}; font-weight: 600;">
                                ${(day.energy_net || 0) >= 0 ? '+' : ''}${day.energy_net || 0}
                            </td>
                        </tr>
                    `}).join('')}
                </tbody>
            </table>
        </div>
    `;
}

function updateTrendsCharts(trends) {
    const reversedTrends = [...trends].reverse();
    const labels = reversedTrends.map(t => {
        const date = new Date(t.date);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });

    // Energy Balance Chart
    const balanceCtx = document.getElementById('trends-balance-chart');
    if (balanceCtx) {
        if (window.trendsBalanceChartInstance) {
            window.trendsBalanceChartInstance.destroy();
        }

        window.trendsBalanceChartInstance = new Chart(balanceCtx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Energy Balance',
                    data: reversedTrends.map(t => t.energy_net || 0),
                    borderColor: 'rgba(99, 102, 241, 1)',
                    backgroundColor: function (context) {
                        const value = context.raw;
                        return value >= 0 ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)';
                    },
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: function (context) {
                        const value = context.raw;
                        return value >= 0 ? 'rgba(16, 185, 129, 1)' : 'rgba(239, 68, 68, 1)';
                    },
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(30, 41, 59, 0.95)',
                        borderColor: 'rgba(99, 102, 241, 0.3)',
                        borderWidth: 1
                    }
                },
                scales: {
                    y: {
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { color: '#94a3b8' }
                    },
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#94a3b8' }
                    }
                }
            }
        });
    }

    // Activity Hours Chart
    const hoursCtx = document.getElementById('trends-hours-chart');
    if (hoursCtx) {
        if (window.trendsHoursChartInstance) {
            window.trendsHoursChartInstance.destroy();
        }

        window.trendsHoursChartInstance = new Chart(hoursCtx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Activity Hours',
                    data: reversedTrends.map(t => t.total_hours || 0),
                    backgroundColor: 'rgba(139, 92, 246, 0.7)',
                    borderColor: 'rgba(139, 92, 246, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(30, 41, 59, 0.95)',
                        borderColor: 'rgba(139, 92, 246, 0.3)',
                        borderWidth: 1
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { color: '#94a3b8' }
                    },
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#94a3b8' }
                    }
                }
            }
        });
    }
}

// ==================== PLAN ====================
async function loadPlan() {
    const container = document.getElementById('plan-content');
    container.innerHTML = '<p class="text-muted">Generating optimized plan...</p>';

    try {
        const data = await fetchPlan();

        if (data.error) {
            container.innerHTML = `<div class="alert alert-error">${data.error}</div>`;
            return;
        }

        let html = `
        <div class="plan-overview" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px;">
            <div class="stat-card">
                <div class="stat-icon" style="background: linear-gradient(135deg, #6366f1, #8b5cf6);">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"></path>
                    </svg>
                </div>
                <div class="stat-details">
                    <div class="stat-value">${data.budget.total}</div>
                    <div class="stat-label">Energy Budget</div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon" style="background: linear-gradient(135deg, #10b981, #059669);">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
                    </svg>
                </div>
                <div class="stat-details">
                    <div class="stat-value">${data.budget.sleep_hours?.toFixed(1) || 0}h</div>
                    <div class="stat-label">Sleep</div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon" style="background: linear-gradient(135deg, #ef4444, #dc2626);">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                    </svg>
                </div>
                <div class="stat-details">
                    <div class="stat-value">${data.budget.rhr || 0}</div>
                    <div class="stat-label">RHR</div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon" style="background: linear-gradient(135deg, #f59e0b, #d97706);">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"></path>
                    </svg>
                </div>
                <div class="stat-details">
                    <div class="stat-value">${data.budget.stress || 0}</div>
                    <div class="stat-label">Stress</div>
                </div>
            </div>
        </div>

        <h3 style="margin: 30px 0 20px 0; font-size: 1.25rem;">Recommended Action Plan (Priority Order)</h3>
        <div class="plan-list">`;

        if (data.plan && data.plan.length > 0) {
            data.plan.forEach((item, index) => {
                html += `
                <div class="plan-item" style="background: var(--bg-secondary); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 20px; margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div style="flex: 1;">
                            <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 10px;">
                                <span style="font-size: 1.5rem; font-weight: 700; color: var(--primary);">${index + 1}</span>
                                <span class="goal-priority p${item.priority}" style="padding: 4px 12px; border-radius: 12px; font-size: 0.75rem; font-weight: 600;">[P${item.priority}]</span>
                                <span style="font-size: 1.1rem; font-weight: 600;">${item.goal}</span>
                            </div>
                            <div style="margin-left: 50px; color: var(--text-secondary); font-size: 0.9rem;">
                                <div>Cost: <span style="color: ${item.cost >= 0 ? 'var(--success)' : 'var(--error)'}; font-weight: 600;">${item.cost >= 0 ? '+' : ''}${item.cost}</span> points</div>
                                <div>Remaining budget after: <strong>${item.remaining_budget}</strong> points</div>
                            </div>
                        </div>
                    </div>
                </div>`;
            });
        } else {
            html += '<p style="text-align: center; color: var(--text-secondary); padding: 40px;">No action items. All your priority goals are scheduled or you have no active P1/recovery goals.</p>';
        }

        html += `</div>`;

        // Recommendations
        if (data.recommendations) {
            html += `
            <h3 style="margin: 40px 0 20px 0; font-size: 1.25rem;">Smart Health Insights</h3>
            <div style="display: grid; gap: 15px;">
                <div style="background: var(--bg-secondary); border-left: 4px solid var(--primary); padding: 20px; border-radius: 8px;">
                    <h4 style="margin: 0 0 10px 0; color: var(--primary);">💤 Sleep</h4>
                    <p style="margin: 0; line-height: 1.6;">${data.recommendations.sleep || 'No sleep data available'}</p>
                </div>
                <div style="background: var(--bg-secondary); border-left: 4px solid var(--success); padding: 20px; border-radius: 8px;">
                    <h4 style="margin: 0 0 10px 0; color: var(--success);">🏃 Activity</h4>
                    <p style="margin: 0; line-height: 1.6;">${data.recommendations.exercise || 'No activity data available'}</p>
                </div>
            </div>`;
        }

        container.innerHTML = html;

    } catch (error) {
        console.error('Error loading plan:', error);
        container.innerHTML = '<p class="error">Failed to load plan.</p>';
    }
}

// ==================== HEALTH METRICS ====================
async function loadHealthMetrics(dateString = null) {
    try {
        const healthData = await fetchTodayHealth(dateString);

        if (healthData) {
            updateHealthMetricsDisplay(healthData);
        } else {
            // Reset metrics if no data
            document.getElementById('metric-sleep-score').textContent = '--';
            document.getElementById('metric-sleep-hours').textContent = '-- hours';
            document.getElementById('metric-rhr').textContent = '--';
            document.getElementById('metric-hr-range').textContent = 'Range: --';
            document.getElementById('metric-stress').textContent = '--';
            document.getElementById('metric-stress-status').textContent = '--';
            document.getElementById('metric-steps').textContent = '--';
        }

        updateHealthTrendsChart();

        // Load Weekly Report
        const reportData = await fetchReport();
        renderWeeklyReport(reportData);

    } catch (error) {
        console.error('Error loading health metrics:', error);
    }
}

function updateHealthMetricsDisplay(health) {
    document.getElementById('metric-sleep-score').textContent = health.sleep_score || '--';
    document.getElementById('metric-sleep-hours').textContent =
        health.sleep_total_min ? `${(health.sleep_total_min / 60).toFixed(1)} hours` : '-- hours';

    document.getElementById('metric-rhr').textContent = health.rhr_avg || '--';
    document.getElementById('metric-hr-range').textContent =
        health.hr_min && health.hr_max ? `Range: ${health.hr_min}-${health.hr_max}` : 'Range: --';

    document.getElementById('metric-stress').textContent = health.stress_avg || '--';
    const stressLevel = health.stress_avg;
    let stressStatus = 'Unknown';
    if (stressLevel && stressLevel > 0) {
        if (stressLevel < 25) stressStatus = 'Low';
        else if (stressLevel < 50) stressStatus = 'Normal';
        else if (stressLevel < 75) stressStatus = 'Elevated';
        else stressStatus = 'High';
    }
    document.getElementById('metric-stress-status').textContent = stressStatus;

    document.getElementById('metric-steps').textContent = health.steps_total || '--';
}

function renderWeeklyReport(reportData) {
    const container = document.getElementById('weekly-report');

    if (!reportData || reportData.error) {
        container.innerHTML = `<p class="error">${reportData?.error || 'Failed to load report'}</p>`;
        return;
    }

    let html = '<div class="report-content">';

    if (reportData.summary) {
        html += `<div class="report-section"><h3>Summary</h3><p>${reportData.summary}</p></div>`;
    }

    if (reportData.insights && reportData.insights.length > 0) {
        html += '<div class="report-section"><h3>Key Insights</h3><ul>';
        reportData.insights.forEach(insight => {
            html += `<li>${insight}</li>`;
        });
        html += '</ul></div>';
    }

    html += '</div>';
    container.innerHTML = html;
}

function updateHealthChart() {
    // Placeholder for health chart
    // Can be implemented with historical health data
}

async function updateHealthTrendsChart() {
    const ctx = document.getElementById('health-chart');
    if (!ctx) return;

    try {
        // Fetch sleep score trends
        const sleepResponse = await fetch(`${API_BASE}/api/health/trends?days=7&metric=sleep_score`);
        const sleepData = await sleepResponse.json();

        // Fetch steps trends
        const stepsResponse = await fetch(`${API_BASE}/api/health/trends?days=7&metric=steps_total`);
        const stepsData = await stepsResponse.json();

        if (!sleepData || sleepData.length === 0) {
            ctx.getContext('2d').clearRect(0, 0, ctx.width, ctx.height);
            return;
        }

        const labels = sleepData.map(d => {
            const date = new Date(d.date);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        });

        const chartData = {
            labels: labels,
            datasets: [
                {
                    label: 'Sleep Score',
                    data: sleepData.map(d => d.value),
                    borderColor: 'rgba(139, 92, 246, 1)',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    yAxisID: 'y'
                },
                {
                    label: 'Steps (÷100)',
                    data: stepsData.map(d => d.value ? d.value / 100 : null),
                    borderColor: 'rgba(16, 185, 129, 1)',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    yAxisID: 'y'
                }
            ]
        };

        // Destroy existing chart if it exists
        if (window.healthChartInstance) {
            window.healthChartInstance.destroy();
        }

        window.healthChartInstance = new Chart(ctx, {
            type: 'line',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: '#e2e8f0',
                            padding: 15,
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(30, 41, 59, 0.9)',
                        titleColor: '#e2e8f0',
                        bodyColor: '#e2e8f0',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: true
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#94a3b8'
                        },
                        title: {
                            display: true,
                            text: 'Score / Steps (÷100)',
                            color: '#94a3b8'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)'
                        },
                        ticks: {
                            color: '#94a3b8'
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error updating health trends chart:', error);
    }
}

// ==================== CHARTS ====================
async function updateEnergyChart(days) {
    const ctx = document.getElementById('energy-chart');
    if (!ctx) return;

    const energyStates = await fetchEnergyStates(days);

    const chartData = {
        labels: Object.keys(energyStates),
        datasets: [{
            data: Object.values(energyStates),
            backgroundColor: [
                'rgba(16, 185, 129, 0.8)',   // Growth
                'rgba(245, 158, 11, 0.8)',   // Consumption
                'rgba(239, 68, 68, 0.8)',    // Internal friction
                'rgba(148, 163, 184, 0.8)'   // Routine
            ],
            borderWidth: 0
        }]
    };

    if (energyChartInstance) {
        energyChartInstance.destroy();
    }

    energyChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#e2e8f0',
                        padding: 15,
                        font: {
                            size: 12
                        }
                    }
                }
            }
        }
    });
}

async function updateBalanceChart(days) {
    const ctx = document.getElementById('balance-chart');
    if (!ctx) return;

    const balance = await fetchEnergyBalance(days);

    const labels = balance.map(b => {
        const date = new Date(b.date);
        return date.toLocaleDateString('en-US', { weekday: 'short' });
    });
    const data = balance.map(b => b.balance);

    const chartData = {
        labels: labels.length > 0 ? labels : ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        datasets: [{
            label: 'Energy Balance',
            data: data.length > 0 ? data : [0, 0, 0, 0, 0, 0, 0],
            borderColor: 'rgba(99, 102, 241, 1)',
            backgroundColor: 'rgba(99, 102, 241, 0.1)',
            tension: 0.4,
            fill: true
        }]
    };

    if (balanceChartInstance) {
        balanceChartInstance.destroy();
    }

    balanceChartInstance = new Chart(ctx, {
        type: 'line',
        data: chartData,
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
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#94a3b8'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    },
                    ticks: {
                        color: '#94a3b8'
                    }
                }
            }
        }
    });
}

// ==================== MODALS ====================
function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// Click outside modal to close
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('active');
    }
});

// ==================== UTILITIES ====================
function showNotification(message, type = 'info') {
    alert(message);
}

function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function refreshDashboard() {
    const datePicker = document.getElementById('dashboard-date-picker');
    const date = datePicker ? datePicker.value : null;
    loadDashboard(date);
}

function refreshHealth() {
    const datePicker = document.getElementById('health-date-picker');
    const date = datePicker ? datePicker.value : null;
    loadHealthMetrics(date);
}

function initializeDatePickers() {
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const dateStr = yesterday.toISOString().split('T')[0];

    const dashboardPicker = document.getElementById('dashboard-date-picker');
    if (dashboardPicker) {
        dashboardPicker.value = dateStr;
        dashboardPicker.addEventListener('change', (e) => {
            loadDashboard(e.target.value);
        });
    }

    const healthPicker = document.getElementById('health-date-picker');
    if (healthPicker) {
        healthPicker.value = dateStr;
        healthPicker.addEventListener('change', (e) => {
            loadHealthMetrics(e.target.value);
        });
    }
}

async function importData(event) {
    event.preventDefault();

    const fileInput = document.getElementById('data-file');
    const file = fileInput.files[0];

    if (!file) {
        alert('Please select a file');
        return;
    }

    document.getElementById('import-data-form').style.display = 'none';
    document.getElementById('import-progress').style.display = 'block';
    document.getElementById('progress-text').textContent = 'Uploading file...';
    document.getElementById('progress-fill').style.width = '30%';

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE}/api/import`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Import failed');

        const result = await response.json();

        document.getElementById('progress-fill').style.width = '100%';
        document.getElementById('progress-text').textContent = `Success! Imported ${result.count || 0} records`;
        document.getElementById('progress-text').style.color = 'var(--success)';

        setTimeout(() => {
            closeModal('import-data-modal');
            document.getElementById('import-data-form').style.display = 'block';
            document.getElementById('import-progress').style.display = 'none';
            document.getElementById('progress-text').style.color = '';
            document.getElementById('progress-fill').style.width = '0%';
            if (currentPage === 'health') {
                loadHealthMetrics();
            }
        }, 2000);

    } catch (error) {
        console.error('Error importing data:', error);
        document.getElementById('progress-fill').style.width = '0%';
        document.getElementById('progress-text').textContent = 'Import failed: ' + error.message;
        document.getElementById('progress-text').style.color = 'var(--error)';

        setTimeout(() => {
            document.getElementById('import-data-form').style.display = 'block';
            document.getElementById('import-progress').style.display = 'none';
            document.getElementById('progress-text').style.color = '';
        }, 3000);
    }
}

// ==================== API FUNCTIONS ====================
async function fetchGoals() {
    try {
        const response = await fetch(`${API_BASE}/api/goals`);
        if (!response.ok) throw new Error('Failed to fetch goals');
        return await response.json();
    } catch (error) {
        console.error('Error fetching goals:', error);
        return [];
    }
}

async function fetchTodayEvents(dateString = null) {
    try {
        let url = `${API_BASE}/api/events/today`;

        if (dateString) {
            url += `?date=${dateString}`;
        } else {
            url += `?offset_days=1`;
        }

        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to fetch events');
        return await response.json();
    } catch (error) {
        console.error('Error fetching events:', error);
        return [];
    }
}

async function fetchEvents(days = 7) {
    try {
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - days);
        const startDateStr = startDate.toISOString().split('T')[0];

        const response = await fetch(`${API_BASE}/api/events?start_date=${startDateStr}`);
        if (!response.ok) throw new Error('Failed to fetch events');
        return await response.json();
    } catch (error) {
        console.error('Error fetching events:', error);
        return [];
    }
}

async function fetchTodayHealth(dateString = null) {
    try {
        let url = `${API_BASE}/api/health/today`;

        if (dateString) {
            url += `?date=${dateString}`;
        } else {
            url += `?offset_days=1`;
        }

        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to fetch health metrics');
        return await response.json();
    } catch (error) {
        console.error('Error fetching health metrics:', error);
        return null;
    }
}

async function fetchEnergyStates(days) {
    try {
        const response = await fetch(`${API_BASE}/api/stats/energy-states?days=${days}`);
        if (!response.ok) throw new Error('Failed to fetch energy states');
        return await response.json();
    } catch (error) {
        console.error('Error fetching energy states:', error);
        return {};
    }
}

async function fetchEnergyBalance(days) {
    try {
        const response = await fetch(`${API_BASE}/api/stats/balance?days=${days}`);
        if (!response.ok) throw new Error('Failed to fetch balance');
        return await response.json();
    } catch (error) {
        console.error('Error fetching balance:', error);
        return [];
    }
}

async function fetchReport() {
    try {
        const response = await fetch(`${API_BASE}/api/report`);
        if (!response.ok) throw new Error('Failed to fetch report');
        return await response.json();
    } catch (error) {
        console.error('Error fetching report:', error);
        return null;
    }
}

async function fetchTrends(days) {
    try {
        const response = await fetch(`${API_BASE}/api/trends?days=${days}`);
        if (!response.ok) throw new Error('Failed to fetch trends');
        return await response.json();
    } catch (error) {
        console.error('Error fetching trends:', error);
        return [];
    }
}

async function fetchPlan() {
    try {
        const response = await fetch(`${API_BASE}/api/plan`);
        if (!response.ok) throw new Error('Failed to fetch plan');
        return await response.json();
    } catch (error) {
        console.error('Error fetching plan:', error);
        return { error: 'Failed to load plan' };
    }
}

async function createGoal(goalData) {
    try {
        const response = await fetch(`${API_BASE}/api/goals`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(goalData)
        });
        if (!response.ok) throw new Error('Failed to create goal');
        return await response.json();
    } catch (error) {
        console.error('Error creating goal:', error);
        throw error;
    }
}

async function updateGoal(goalId, goalData) {
    try {
        const response = await fetch(`${API_BASE}/api/goals/${goalId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(goalData)
        });
        if (!response.ok) throw new Error('Failed to update goal');
        return await response.json();
    } catch (error) {
        console.error('Error updating goal:', error);
        throw error;
    }
}

async function createEvent(eventData) {
    try {
        const response = await fetch(`${API_BASE}/api/events`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(eventData)
        });
        if (!response.ok) throw new Error('Failed to create event');
        return await response.json();
    } catch (error) {
        console.error('Error creating event:', error);
        throw error;
    }
}

async function archiveGoalById(goalId) {
    try {
        const response = await fetch(`${API_BASE}/api/goals/${goalId}/archive`, {
            method: 'PUT'
        });
        if (!response.ok) throw new Error('Failed to archive goal');
        return await response.json();
    } catch (error) {
        console.error('Error archiving goal:', error);
        throw error;
    }
}

// ==================== MODAL FUNCTIONS ====================

function showLogEventModal() {
    const modal = document.getElementById('log-event-modal');
    if (!modal) return;

    // Ensure goals are loaded
    if (!goalsCache || goalsCache.length === 0) {
        fetchGoals().then(goals => {
            goalsCache = goals;
            populateGoalDropdown();
        }).catch(err => console.error('Error loading goals for modal:', err));
    } else {
        populateGoalDropdown();
    }

    function populateGoalDropdown() {
        const goalSelect = document.getElementById('event-goal');
        if (goalSelect) {
            goalSelect.innerHTML = '<option value="">None</option>';
            if (goalsCache && goalsCache.length > 0) {
                goalsCache.forEach(goal => {
                    // API returns is_active (1 or true), checking that instead of status string
                    if (goal.is_active) {
                        const option = document.createElement('option');
                        option.value = goal.goal_id;
                        option.textContent = `${goal.goal_name} (P${goal.priority_level})`;
                        goalSelect.appendChild(option);
                    }
                });
            }
        }
    }

    // Set default date/time
    const now = new Date();
    const dateInput = document.getElementById('event-date');
    const timeInput = document.getElementById('event-time');

    if (dateInput) dateInput.value = now.toISOString().split('T')[0];
    if (timeInput) timeInput.value = now.toTimeString().slice(0, 5);

    modal.style.display = 'flex';
}

function showImportDataModal() {
    const modal = document.getElementById('import-data-modal');
    if (modal) {
        modal.style.display = 'flex';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
}

async function logEvent(event) {
    event.preventDefault();

    const dateValue = document.getElementById('event-date').value;
    const timeValue = document.getElementById('event-time').value;
    const timestamp = new Date(`${dateValue}T${timeValue}`).toISOString();

    const eventData = {
        activity: document.getElementById('event-activity').value,
        duration_minutes: parseInt(document.getElementById('event-duration').value),
        goal_id: document.getElementById('event-goal').value || null,
        key_state: document.getElementById('event-state').value,
        physical_score: parseInt(document.getElementById('event-physical').value),
        mental_score: parseInt(document.getElementById('event-mental').value),
        emotional_score: parseInt(document.getElementById('event-emotional').value),
        notes: document.getElementById('event-notes').value,
        timestamp_start: timestamp
    };

    try {
        await createEvent(eventData);
        closeModal('log-event-modal');
        document.getElementById('log-event-form').reset();
        if (currentPage === 'journal') {
            await loadJournal(90);
        } else if (currentPage === 'dashboard') {
            await loadDashboard();
        }
        // Show notification if function exists, otherwise alert
        if (typeof showNotification === 'function') {
            showNotification('Event logged successfully!', 'success');
        } else {
            alert('Event logged successfully!');
        }
    } catch (error) {
        console.error('Error logging event:', error);
        if (typeof showNotification === 'function') {
            showNotification('Error: ' + error.message, 'error');
        } else {
            alert('Error: ' + error.message);
        }
    }
}

// Make functions global
window.showLogEventModal = showLogEventModal;
window.showImportDataModal = showImportDataModal;
window.closeModal = closeModal;
window.logEvent = logEvent;
window.fetchGoals = fetchGoals;
