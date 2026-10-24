/* Shared behaviour for the admin layout (base_admin.html).
 *
 * - Mobile drawer: hamburger opens the sidebar as a slide-in drawer,
 *   overlay click / Escape / any nav click closes it, body scroll locks.
 * - Desktop collapse: sidebar becomes an icon rail; the preference is
 *   persisted in localStorage and applied pre-paint by the inline
 *   script in base_admin.html.
 * - "Expenses" nav item: sidebar link to the Analytics page's expense
 *   section (#manage-expenses); highlighted client-side while the
 *   fragment is present.
 * - Escape closes any admin modal (.admin-modal-overlay.active) —
 *   complements the per-page click handlers.
 *
 * Conventions: vanilla JS, no dependencies, min-width-769px = desktop.
 */
(function () {
    'use strict';

    var docEl = document.documentElement;
    var body = document.body;
    var STORAGE_KEY = 'admin.sidebar';

    var toggleBtn = document.getElementById('admin-nav-toggle');
    var overlay = document.getElementById('admin-drawer-overlay');
    var sidebar = document.getElementById('admin-sidebar');
    var collapseBtn = document.getElementById('admin-sidebar-collapse');

    /* ------------------------------------------------------------ drawer */

    function drawerOpen() {
        return body.classList.contains('admin-drawer-open');
    }

    function openDrawer() {
        body.classList.add('admin-drawer-open');
        body.style.overflow = 'hidden';   // lock background scrolling
        if (toggleBtn) {
            toggleBtn.setAttribute('aria-expanded', 'true');
            toggleBtn.setAttribute('aria-label', 'Close navigation menu');
        }
        var firstLink = sidebar ? sidebar.querySelector('.admin-nav-item') : null;
        if (firstLink) firstLink.focus();
    }

    function closeDrawer(refocusToggle) {
        body.classList.remove('admin-drawer-open');
        body.style.overflow = '';
        if (toggleBtn) {
            toggleBtn.setAttribute('aria-expanded', 'false');
            toggleBtn.setAttribute('aria-label', 'Open navigation menu');
            if (refocusToggle) toggleBtn.focus();
        }
    }

    if (toggleBtn) {
        toggleBtn.addEventListener('click', function () {
            if (drawerOpen()) closeDrawer(false);
            else openDrawer();
        });
    }
    if (overlay) {
        overlay.addEventListener('click', function () { closeDrawer(true); });
    }

    // Any navigation inside the drawer closes it after the click lands.
    if (sidebar) {
        sidebar.addEventListener('click', function (ev) {
            var target = ev.target.closest('.admin-nav-item, .admin-logout-link');
            if (target && drawerOpen()) closeDrawer(false);
        });
    }

    /* ------------------------------------------------------------ collapse */

    function syncCollapseButton() {
        if (!collapseBtn) return;
        var collapsed = docEl.classList.contains('admin-collapsed');
        collapseBtn.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
        collapseBtn.setAttribute('aria-label', collapsed ? 'Expand sidebar' : 'Collapse sidebar');
    }

    if (collapseBtn) {
        syncCollapseButton();  // the inline head script may already have set the class
        collapseBtn.addEventListener('click', function () {
            var collapsed = docEl.classList.toggle('admin-collapsed');
            try {
                localStorage.setItem(STORAGE_KEY, collapsed ? 'collapsed' : 'expanded');
            } catch (e) { /* preference is cosmetic; ignore storage failures */ }
            syncCollapseButton();
        });
    }

    /* ------------------------------------------------------------ modals */

    document.addEventListener('keydown', function (ev) {
        if (ev.key !== 'Escape') return;
        if (drawerOpen()) {
            closeDrawer(true);
            return;
        }
        document.querySelectorAll('.admin-modal-overlay.active').forEach(function (modal) {
            modal.classList.remove('active');
        });
    });

    /* ------------------------------------------------------------ expenses link */

    var expensesLink = document.querySelector('.admin-nav-expenses');
    var analyticsLink = document.querySelector('.admin-nav-item[href$="/admin/analytics"]');
    var analyticsPath = analyticsLink ? analyticsLink.getAttribute('href').split('#')[0] : '/admin/analytics';

    function syncExpensesActive() {
        if (!expensesLink || !analyticsLink) return;
        // Only the Analytics page ever swaps between the Analytics and
        // Expenses items; elsewhere the server-rendered state stands.
        if (window.location.pathname !== analyticsPath) {
            expensesLink.classList.remove('active');
            return;
        }
        var onExpenses = window.location.hash === '#manage-expenses';
        expensesLink.classList.toggle('active', onExpenses);
        analyticsLink.classList.toggle('active', !onExpenses);
    }

    window.addEventListener('hashchange', syncExpensesActive);
    syncExpensesActive();

    /* ------------------------------------------------------------ leave-the-drawer hygiene */

    window.addEventListener('resize', function () {
        if (window.innerWidth > 768 && drawerOpen()) closeDrawer(false);
    });
})();
