/* Admin analytics page.
 *
 * Fetches one payload per (range, interval, metric) from
 * /api/admin/analytics and renders:
 *   - KPI cards (replacing the server-rendered skeletons)
 *   - orders / revenue-vs-expense / accounts / status charts (Chart.js)
 *   - trending items list
 *   - expense overview + expense management table
 *
 * Conventions: vanilla JS like the site's other scripts, CSRF read from
 * the base_admin meta tag, chart colors keyed to tokens.css palette.
 */
(function () {
    'use strict';

    var els = {
        range: document.getElementById('analytics-range'),
        refresh: document.getElementById('analytics-refresh'),
        updated: document.getElementById('analytics-updated'),
        error: document.getElementById('analytics-error'),
        errorText: document.getElementById('analytics-error-text'),
        kpis: document.getElementById('analytics-kpis'),
        interval: document.getElementById('analytics-interval'),
        metric: document.getElementById('trending-metric'),
        ordersCanvas: document.getElementById('chart-orders'),
        ordersEmpty: document.getElementById('orders-empty'),
        ordersCaption: document.getElementById('orders-caption'),
        statusCanvas: document.getElementById('chart-status'),
        statusEmpty: document.getElementById('status-empty'),
        mixCanvas: document.getElementById('chart-mix'),
        mixEmpty: document.getElementById('mix-empty'),
        mixCaption: document.getElementById('mix-caption'),
        accountsCanvas: document.getElementById('chart-accounts'),
        accountsEmpty: document.getElementById('accounts-empty'),
        trendingList: document.getElementById('trending-list'),
        trendingEmpty: document.getElementById('trending-empty'),
        expenseChip: document.getElementById('expense-chip'),
        expenseCanvas: document.getElementById('chart-expenses'),
        expenseEmpty: document.getElementById('expenses-empty'),
        expenseCaption: document.getElementById('expense-caption'),
        expenseForm: document.getElementById('expense-form'),
        expenseMsg: document.getElementById('expense-form-msg'),
        expenseRows: document.getElementById('expense-rows'),
        expenseTableEmpty: document.getElementById('expense-table-empty'),
        expenseSubmit: document.getElementById('expense-submit'),
    };

    var state = { range: '30', interval: 'day', metric: 'qty' };
    var charts = { orders: null, status: null, mix: null, accounts: null, expenses: null };
    var pending = false;
    var firstLoad = true;

    function getCsrfToken() {
        var meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute('content') : '';
    }

    var inr = new Intl.NumberFormat('en-IN', {
        style: 'currency', currency: 'INR', minimumFractionDigits: 2, maximumFractionDigits: 2,
    });
    var inrCompact = new Intl.NumberFormat('en-IN', {
        style: 'currency', currency: 'INR', maximumFractionDigits: 0,
    });

    function money(v) { return inr.format(v); }

    function pctText(payload) {
        if (payload.prev === null || payload.prev === undefined) {
            return 'No comparison data';
        }
        // The current period's size: order/customer cards use count,
        // the revenue card has no count field (orders is the proxy).
        var cur = payload.count !== undefined ? payload.count :
            (payload.orders !== undefined ? payload.orders : payload.total);
        if (Number(payload.prev) === 0 && Number(cur) > 0) {
            return 'New — no ' + payload.prev_label + ' activity';
        }
        if (payload.pct === null || payload.pct === undefined) {
            return 'No change vs ' + payload.prev_label;
        }
        var arrow = payload.pct >= 0 ? '▲' : '▼';
        var cls = payload.pct >= 0 ? 'kpi-delta-up' : 'kpi-delta-down';
        return '<span class="' + cls + '">' + arrow + ' ' + Math.abs(payload.pct) + '%</span> vs ' + payload.prev_label;
    }

    /* ------------------------------------------------------------ charts */

    function baseOptions() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 300 },
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: {
                    labels: {
                        color: 'rgba(255,255,255,0.7)',
                        font: { family: 'Inter', size: 11 },
                        boxWidth: 12, boxHeight: 12,
                    },
                },
                tooltip: {
                    backgroundColor: 'rgba(10,10,10,0.95)',
                    borderColor: 'rgba(255,255,255,0.2)',
                    borderWidth: 1,
                    titleColor: '#f5c542',
                    bodyColor: 'rgba(255,255,255,0.9)',
                    titleFont: { family: 'Inter', weight: 'bold' },
                    bodyFont: { family: 'Inter' },
                },
            },
            scales: {
                x: {
                    ticks: { color: 'rgba(255,255,255,0.5)', font: { family: 'Inter', size: 10 } },
                    grid: { color: 'rgba(255,255,255,0.06)' },
                },
                y: {
                    beginAtZero: true,
                    ticks: { color: 'rgba(255,255,255,0.5)', font: { family: 'Inter', size: 10 } },
                    grid: { color: 'rgba(255,255,255,0.06)' },
                },
            },
        };
    }

    function destroy(chartsRef, key) {
        if (chartsRef[key]) {
            chartsRef[key].destroy();
            chartsRef[key] = null;
        }
    }

    function moneyAxis(opts) {
        opts.scales.y.ticks.callback = function (value) { return inrCompact.format(value); };
        return opts;
    }

    function renderOrdersChart(series) {
        var opts = baseOptions();
        opts.scales.x.title = { display: true, text: series.interval === 'month' ? 'Month' : (series.interval === 'week' ? 'Week' : 'Day'), color: 'rgba(255,255,255,0.5)', font: { family: 'Inter', size: 10 } };
        opts.scales.y.title = { display: true, text: 'Orders', color: 'rgba(255,255,255,0.5)', font: { family: 'Inter', size: 10 } };
        opts.plugins.tooltip.callbacks = {
            title: function (items) { return items[0].label; },
            label: function (item) {
                var name = item.dataset.label;
                var v = item.parsed.y;
                return name + ': ' + v + (v === 1 ? ' order' : ' orders');
            },
        };
        var total = 0;
        series.orders_paid.forEach(function (v) { total += v; });
        series.orders_other.forEach(function (v) { total += v; });
        var hasData = total > 0;
        els.ordersEmpty.hidden = hasData;
        els.ordersCanvas.hidden = !hasData;
        if (!hasData) { destroy(charts, 'orders'); return; }
        destroy(charts, 'orders');
        charts.orders = new Chart(els.ordersCanvas, {
            type: 'bar',
            data: {
                labels: series.labels,
                datasets: [
                    { label: 'Paid', data: series.orders_paid, backgroundColor: 'rgba(76,175,80,0.55)', hoverBackgroundColor: 'rgba(76,175,80,0.8)', borderRadius: 3, stack: 'orders' },
                    { label: 'Not paid', data: series.orders_other, backgroundColor: 'rgba(245,197,66,0.45)', hoverBackgroundColor: 'rgba(245,197,66,0.7)', borderRadius: 3, stack: 'orders' },
                ],
            },
            options: opts,
        });
    }

    function renderMixChart(series) {
        var opts = moneyAxis(baseOptions());
        opts.scales.y.title = { display: true, text: 'Amount (₹)', color: 'rgba(255,255,255,0.5)', font: { family: 'Inter', size: 10 } };
        opts.plugins.tooltip.callbacks = {
            title: function (items) { return items[0].label; },
            label: function (item) { return item.dataset.label + ': ' + money(item.parsed.y); },
        };
        var revenueTotal = 0, expenseTotal = 0;
        series.revenue.forEach(function (v) { revenueTotal += v; });
        series.expenses.forEach(function (v) { expenseTotal += v; });
        var hasData = revenueTotal > 0 || expenseTotal > 0;
        els.mixEmpty.hidden = hasData;
        els.mixCanvas.hidden = !hasData;
        if (!hasData) { destroy(charts, 'mix'); return; }
        destroy(charts, 'mix');
        charts.mix = new Chart(els.mixCanvas, {
            data: {
                labels: series.labels,
                datasets: [
                    { type: 'bar', label: 'Expenses', data: series.expenses, backgroundColor: 'rgba(255,107,107,0.5)', hoverBackgroundColor: 'rgba(255,107,107,0.75)', borderRadius: 3 },
                    { type: 'line', label: 'Revenue (paid orders)', data: series.revenue, borderColor: '#f5c542', backgroundColor: 'rgba(245,197,66,0.15)', fill: true, tension: 0.35, pointRadius: 2, pointBackgroundColor: '#f5c542', borderWidth: 2 },
                ],
            },
            options: opts,
        });
    }

    function renderAccountsChart(series) {
        var opts = baseOptions();
        opts.scales.y.title = { display: true, text: 'New accounts', color: 'rgba(255,255,255,0.5)', font: { family: 'Inter', size: 10 } };
        opts.plugins.legend.display = false;
        opts.plugins.tooltip.callbacks = {
            title: function (items) { return items[0].label; },
            label: function (item) {
                var v = item.parsed.y;
                return v + ' new ' + (v === 1 ? 'account' : 'accounts');
            },
        };
        var total = 0;
        series.new_accounts.forEach(function (v) { total += v; });
        var hasData = total > 0;
        els.accountsEmpty.hidden = hasData;
        els.accountsCanvas.hidden = !hasData;
        if (!hasData) { destroy(charts, 'accounts'); return; }
        destroy(charts, 'accounts');
        charts.accounts = new Chart(els.accountsCanvas, {
            type: 'line',
            data: {
                labels: series.labels,
                datasets: [{ label: 'New accounts', data: series.new_accounts, borderColor: 'rgba(255,255,255,0.85)', backgroundColor: 'rgba(255,255,255,0.08)', fill: true, tension: 0.35, pointRadius: 2, pointBackgroundColor: 'rgba(255,255,255,0.9)', borderWidth: 2 }],
            },
            options: opts,
        });
    }

    var STATUS_COLORS = {
        paid: 'rgba(76,175,80,0.75)',
        pending: 'rgba(245,197,66,0.75)',
        cancelled: 'rgba(255,107,107,0.75)',
        void: 'rgba(255,255,255,0.3)',
    };
    var FALLBACK_COLORS = ['rgba(245,197,66,0.75)', 'rgba(255,255,255,0.3)', 'rgba(255,107,107,0.75)', 'rgba(76,175,80,0.75)'];

    function renderStatusChart(statusCounts) {
        var labels = Object.keys(statusCounts);
        var hasData = labels.length > 0;
        els.statusEmpty.hidden = hasData;
        els.statusCanvas.hidden = !hasData;
        if (!hasData) { destroy(charts, 'status'); return; }
        var values = labels.map(function (s) { return statusCounts[s]; });
        var colors = labels.map(function (s, i) { return STATUS_COLORS[s] || FALLBACK_COLORS[i % FALLBACK_COLORS.length]; });
        var opts = baseOptions();
        opts.interaction = { mode: 'nearest', intersect: true };
        opts.plugins.legend.position = 'right';
        opts.plugins.tooltip.callbacks = {
            label: function (item) {
                var total = values.reduce(function (a, b) { return a + b; }, 0);
                var pct = total ? Math.round(item.parsed / total * 100) : 0;
                return item.label + ': ' + item.parsed + ' (' + pct + '%)';
            },
        };
        destroy(charts, 'status');
        charts.status = new Chart(els.statusCanvas, {
            type: 'doughnut',
            data: { labels: labels, datasets: [{ data: values, backgroundColor: colors, borderColor: 'rgba(0,0,0,0.6)', borderWidth: 2 }] },
            options: opts,
        });
    }

    function renderExpenseChart(byCategory) {
        var labels = Object.keys(byCategory);
        var hasData = labels.length > 0;
        els.expenseEmpty.hidden = hasData;
        els.expenseCanvas.hidden = !hasData;
        if (!hasData) { destroy(charts, 'expenses'); return; }
        var values = labels.map(function (c) { return byCategory[c]; });
        var opts = moneyAxis(baseOptions());
        opts.indexAxis = 'y';
        opts.scales.x.title = { display: true, text: 'Amount (₹)', color: 'rgba(255,255,255,0.5)', font: { family: 'Inter', size: 10 } };
        opts.plugins.legend.display = false;
        opts.plugins.tooltip.callbacks = {
            label: function (item) { return 'Spent: ' + money(item.parsed.x); },
        };
        destroy(charts, 'expenses');
        charts.expenses = new Chart(els.expenseCanvas, {
            type: 'bar',
            data: { labels: labels, datasets: [{ data: values, backgroundColor: 'rgba(255,107,107,0.55)', hoverBackgroundColor: 'rgba(255,107,107,0.8)', borderRadius: 3 }] },
            options: opts,
        });
    }

    /* ------------------------------------------------------------ KPI cards */

    var ICONS = {
        lifetime: '<svg class="kpi-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 6h16M4 12h10M4 18h7"/></svg>',
        month: '<svg class="kpi-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 9h18M8 3v4M16 3v4"/></svg>',
        users: '<svg class="kpi-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="9" cy="8" r="3.5"/><path d="M3 20c0-3.3 2.7-5 6-5s6 1.7 6 5"/><circle cx="17.5" cy="9.5" r="2.5"/><path d="M17 15.5c2.5.4 4 1.9 4 4.5"/></svg>',
        accounts: '<svg class="kpi-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-6 8-6s8 2 8 6"/></svg>',
        revenue: '<svg class="kpi-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 20V10M10 20V4M16 20v-8M22 20H2"/></svg>',
        aov: '<svg class="kpi-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v10M9.5 9.5c0-1.4 1.1-2.2 2.5-2.2s2.5.8 2.5 2.1c0 2.6-5 2.2-5 4.6 0 1.3 1.1 2.1 2.5 2.1s2.5-.8 2.5-2.1"/></svg>',
    };

    function firstLineOfIconRow(icon, label) {
        return '<div class="kpi-head"><p class="stat-label">' + label + '</p>' + icon + '</div>';
    }

    function renderKpis(kpis) {
        var lifetime = kpis.lifetime_orders;
        var lifetimeParts = ['paid: ' + (lifetime.status.paid || 0)];
        ['pending', 'cancelled', 'void'].forEach(function (s) {
            if (lifetime.status[s]) lifetimeParts.push(s + ': ' + lifetime.status[s]);
        });

        var orders = kpis.orders_period;
        var customers = kpis.customers_period;
        var accounts = kpis.accounts;
        var revenue = kpis.revenue;
        var aov = kpis.aov;

        var html = '';
        html += '<div class="stat-card">' + firstLineOfIconRow(ICONS.lifetime, 'Lifetime Orders') +
            '<p class="stat-value">' + lifetime.count + '</p>' +
            '<p class="kpi-caption">' + lifetimeParts.join(' · ') + '</p></div>';

        html += '<div class="stat-card">' + firstLineOfIconRow(ICONS.month, 'Orders in Period') +
            '<p class="stat-value">' + orders.count + '</p>' +
            '<p class="kpi-caption">' + pctText(orders) + '</p></div>';

        html += '<div class="stat-card">' + firstLineOfIconRow(ICONS.users, 'Customers in Period') +
            '<p class="stat-value">' + customers.count + '</p>' +
            '<p class="kpi-caption">' + pctText(customers) +
            (customers.repeat ? ' · ' + customers.repeat + ' repeat' : '') + '</p></div>';

        html += '<div class="stat-card">' + firstLineOfIconRow(ICONS.accounts, 'Total Accounts') +
            '<p class="stat-value">' + accounts.total + '</p>' +
            '<p class="kpi-caption">admin: ' + accounts.admins + ' · customers: ' + accounts.customers + '</p></div>';

        html += '<div class="stat-card">' + firstLineOfIconRow(ICONS.revenue, 'Revenue in Period') +
            '<p class="stat-value">' + money(revenue.total) + '</p>' +
            '<p class="kpi-caption">' + pctText(revenue) +
            (revenue.tips > 0 ? ' · incl. ' + money(revenue.tips) + ' tips' : '') + '</p></div>';

        html += '<div class="stat-card">' + firstLineOfIconRow(ICONS.aov, 'Avg Order Value') +
            '<p class="stat-value">' + (aov.value === null ? '—' : money(aov.value)) + '</p>' +
            '<p class="kpi-caption">' + aov.orders + ' paid ' + (aov.orders === 1 ? 'order' : 'orders') + '</p></div>';

        els.kpis.innerHTML = html;
    }

    /* ------------------------------------------------------------ lists */

    function renderTrending(trending) {
        els.trendingList.innerHTML = '';
        var items = trending.items;
        if (!items.length) {
            els.trendingEmpty.hidden = false;
            return;
        }
        els.trendingEmpty.hidden = true;
        var html = '';
        items.forEach(function (item, i) {
            var thumb;
            if (item.image) {
                thumb = '<img class="trending-thumb" src="/static/' + item.image.replace(/"/g, '&quot;') + '" alt="" loading="lazy">';
            } else {
                thumb = '<span class="trending-thumb-fallback" aria-hidden="true">' + (item.title.charAt(0) || '?') + '</span>';
            }
            if (state.metric === 'qty') {
                html += '<li class="trending-item">' +
                    '<span class="trending-rank" aria-hidden="true">' + (i + 1) + '</span>' + thumb +
                    '<span class="trending-name"><strong>' + escapeHtml(item.title) + '</strong>' +
                    '<small>' + item.orders + ' ' + (item.orders === 1 ? 'order contains' : 'orders contain') + ' it · ' + item.share + '% of items sold</small></span>' +
                    '<span class="trending-value"><strong>' + item.qty + ' sold</strong>' +
                    '<small>' + money(item.revenue) + '</small></span></li>';
            } else {
                html += '<li class="trending-item">' +
                    '<span class="trending-rank" aria-hidden="true">' + (i + 1) + '</span>' + thumb +
                    '<span class="trending-name"><strong>' + escapeHtml(item.title) + '</strong>' +
                    '<small>' + item.orders + ' ' + (item.orders === 1 ? 'order contains' : 'orders contain') + ' it · ' + item.share + '% of revenue</small></span>' +
                    '<span class="trending-value"><strong>' + money(item.revenue) + '</strong>' +
                    '<small>' + item.qty + ' sold</small></span></li>';
            }
        });
        els.trendingList.innerHTML = html;
    }

    function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function renderCaption(el, text) {
        if (!text) { el.hidden = true; return; }
        el.hidden = false;
        el.textContent = text;
    }

    /* ------------------------------------------------------------ expenses */

    function renderExpenseSummary(expenses) {
        if (expenses.count > 0) {
            els.expenseChip.hidden = false;
            els.expenseChip.textContent = money(expenses.total) + ' · ' + expenses.count + ' ' +
                (expenses.count === 1 ? 'record' : 'records');
        } else {
            els.expenseChip.hidden = true;
        }
        renderExpenseChart(expenses.by_category);
        renderCaption(els.expenseCaption, '');

        var html = '';
        expenses.recent.forEach(function (e) {
            var d = new Date(e.spent_on + 'T00:00:00');
            var label = d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
            html += '<tr><td>' + escapeHtml(e.title) + '</td>' +
                '<td>' + escapeHtml(e.category) + '</td>' +
                '<td>' + money(e.amount) + '</td>' +
                '<td>' + label + '</td>' +
                '<td><button type="button" class="analytics-delete-btn" data-expense-id="' + e.id + '">' +
                'Delete</button></td></tr>';
        });
        els.expenseRows.innerHTML = html;
        els.expenseTableEmpty.hidden = expenses.count > 0;
    }

    function showFormMsg(kind, text) {
        els.expenseMsg.hidden = false;
        els.expenseMsg.className = 'analytics-form-msg ' + kind;
        els.expenseMsg.textContent = text;
    }

    els.expenseForm.addEventListener('submit', function (ev) {
        ev.preventDefault();
        if (!els.expenseForm.reportValidity()) return;
        var amount = els.expenseForm.amount.value.trim();
        var body = {
            title: els.expenseForm.title.value.trim(),
            category: els.expenseForm.category.value,
            amount: amount === '' ? null : Number(amount),
            spent_on: els.expenseForm.spent_on.value,
        };
        els.expenseSubmit.disabled = true;
        fetch('/api/admin/expenses', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
            body: JSON.stringify(body),
        }).then(function (resp) {
            return resp.json().then(function (json) { return { ok: resp.ok, json: json }; });
        }).then(function (result) {
            if (!result.ok) {
                showFormMsg('error', result.json.error || 'Could not add the expense.');
                return;
            }
            els.expenseForm.reset();
            els.expenseForm.spent_on.value = els.expenseForm.spent_on.max;
            showFormMsg('success', 'Expense recorded.');
            return load();
        }).catch(function () {
            showFormMsg('error', 'Network error — the expense was not saved.');
        }).finally(function () {
            els.expenseSubmit.disabled = false;
        });
    });

    els.expenseRows.addEventListener('click', function (ev) {
        var button = ev.target.closest('.analytics-delete-btn');
        if (!button || button.disabled) return;
        button.disabled = true;
        fetch('/api/admin/expenses/' + button.getAttribute('data-expense-id') + '/delete', {
            method: 'POST',
            headers: { 'X-CSRFToken': getCsrfToken() },
        }).then(function (resp) {
            if (!resp.ok) {
                button.disabled = false;
                showFormMsg('error', 'Could not delete the expense.');
                return;
            }
            showFormMsg('success', 'Expense deleted.');
            return load();
        }).catch(function () {
            button.disabled = false;
            showFormMsg('error', 'Network error — the expense was not deleted.');
        });
    });

    /* ------------------------------------------------------------ main load */

    function showError(message) {
        els.error.hidden = false;
        els.errorText.textContent = message || 'Could not load analytics. Please try again.';
    }

    function clearError() {
        els.error.hidden = true;
        els.errorText.textContent = '';
    }

    function load() {
        if (pending) return;
        pending = true;
        els.refresh.disabled = true;

        var params = new URLSearchParams({ range: state.range, metric: state.metric });
        if (state.interval) params.set('interval', state.interval);

        fetch('/api/admin/analytics?' + params.toString(), { headers: { 'Accept': 'application/json' } })
            .then(function (resp) {
                return resp.json().then(function (json) { return { ok: resp.ok, json: json }; });
            })
            .then(function (result) {
                if (!result.ok) {
                    // Server errors carry their own message; keep previous data visible.
                    showError((result.json && result.json.error) || '');
                    return;
                }
                clearError();
                var data = result.json;
                if (data.coerced_note) {
                    if (els.interval) {
                        // Reflect the server's enforced interval in the switch.
                        Array.prototype.forEach.call(els.interval.querySelectorAll('button'), function (b) {
                            b.classList.toggle('active', b.getAttribute('data-interval') === data.interval);
                        });
                    }
                    state.interval = data.interval;
                }
                renderKpis(data.kpis);
                renderOrdersChart(data.series);
                renderStatusChart(data.status_counts);
                renderMixChart(data.series);
                renderAccountsChart(data.series);
                renderTrending(data.trending);
                renderExpenseSummary(data.expenses);
                renderCaption(els.ordersCaption, data.coerced_note || '');
                els.updated.hidden = false;
                els.updated.textContent = 'Updated ' + new Date(data.generated_at).toLocaleTimeString('en-IN',
                    { hour: 'numeric', minute: '2-digit' }) + ' IST · range: ' + data.range_label;
            })
            .catch(function () {
                showError('Could not reach the server. Check your connection and press Refresh.');
            })
            .finally(function () {
                pending = false;
                firstLoad = false;
                els.refresh.disabled = false;
            });
    }

    /* ------------------------------------------------------------ events */

    els.range.addEventListener('change', function () {
        state.range = els.range.value;
        // Reset the manual interval choice to the default for this range.
        state.interval = defaultIntervalFor(state.range);
        syncSegment(els.interval, state.interval);
        load();
    });

    els.refresh.addEventListener('click', load);

    els.interval.addEventListener('click', function (ev) {
        var button = ev.target.closest('button[data-interval]');
        if (!button) return;
        syncSegment(els.interval, button.getAttribute('data-interval'));
        state.interval = button.getAttribute('data-interval');
        load();
    });

    els.metric.addEventListener('click', function (ev) {
        var button = ev.target.closest('button[data-metric]');
        if (!button) return;
        syncSegment(els.metric, button.getAttribute('data-metric'));
        state.metric = button.getAttribute('data-metric');
        load();
    });

    /* Highlight one button in a segmented switch. */
    function syncSegment(container, activeValue) {
        Array.prototype.forEach.call(container.querySelectorAll('button'), function (b) {
            var value = b.getAttribute('data-interval') || b.getAttribute('data-metric');
            b.classList.toggle('active', value === activeValue);
        });
    }

    /* Client-side mirror of the server's _auto_interval so the switch
       always shows what will be requested. The server still
       re-validates and may coerce (surfaces as coerced_note). */
    function defaultIntervalFor(range) {
        if (range === '7' || range === '30' || range === 'month' || range === 'last_month') return 'day';
        if (range === '90') return 'week';
        return 'month'; // year, all time
    }

    load();
})();
