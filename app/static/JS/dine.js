/* =====================================================
   HOMEPAGE — "Dine with us" location picker
   -----------------------------------------------------
   Three location cards (a radiogroup) on the left; one
   live Google map on the right. Selecting a card swaps
   the embedded map, its title, and the section's
   "Get directions" link to that location.

   Per-location map + directions URLs live on each card
   as data attributes in index.html — the single source
   of truth, so new locations are a markup-only change.
   ===================================================== */
(function () {
    'use strict';

    var LOAD_TIMEOUT = 10000; /* veil yields to a graceful fallback after this */

    var group = document.querySelector('.location-cards');
    var cards = group ? Array.prototype.slice.call(group.querySelectorAll('.location-card')) : [];
    var frame = document.getElementById('location-map-frame');
    var mapWrap = frame ? frame.closest('.location-map') : null;
    var failMsg = mapWrap ? mapWrap.querySelector('.map-fail') : null;
    var failLink = failMsg ? failMsg.querySelector('a') : null;
    var directionsLink = document.querySelector('[data-directions-link]');

    if (!group || !cards.length || !frame || !mapWrap) return;

    var failTimer = null;

    /* A chalk veil covers the map while a new embed loads;
       if the embed never arrives, offer the plain
       Google Maps link instead of a stuck spinner. */
    function armFailWatch(card) {
        window.clearTimeout(failTimer);
        failTimer = window.setTimeout(function () {
            if (mapWrap.classList.contains('is-loading')) {
                mapWrap.classList.remove('is-loading');
                mapWrap.classList.add('has-failed');
                if (failLink) failLink.href = String(card.dataset.map || '').replace('&output=embed', '');
                if (failMsg) failMsg.hidden = false;
            }
        }, LOAD_TIMEOUT);
    }

    function swapMap(card) {
        var src = card.dataset.map || '';
        if (frame.getAttribute('src') === src) return;
        mapWrap.classList.remove('has-failed');
        if (failMsg) failMsg.hidden = true;
        mapWrap.classList.add('is-loading');
        armFailWatch(card);
        var name = card.querySelector('.location-card-name');
        frame.title = 'Map — ' + (name ? name.textContent.trim() : 'location');
        frame.setAttribute('src', src);
    }

    function select(index, moveFocus) {
        var card = cards[index];
        if (!card) return;
        var already = card.classList.contains('is-selected');
        cards.forEach(function (c, i) {
            var on = i === index;
            c.classList.toggle('is-selected', on);
            c.setAttribute('aria-checked', on ? 'true' : 'false');
            c.tabIndex = on ? 0 : -1;
        });
        if (!already) {
            swapMap(card);
            if (directionsLink) directionsLink.setAttribute('href', card.dataset.directions || '#');
        }
        if (moveFocus) card.focus();
    }

    frame.addEventListener('load', function () {
        window.clearTimeout(failTimer);
        mapWrap.classList.remove('is-loading');
    });

    cards.forEach(function (card, i) {
        card.addEventListener('click', function () { select(i, false); });
    });

    /* Radiogroup keys: arrows move and select, Home/End jump */
    group.addEventListener('keydown', function (e) {
        var idx = cards.indexOf(document.activeElement);
        if (idx < 0) return;
        var next = null;
        if (e.key === 'ArrowDown' || e.key === 'ArrowRight') next = (idx + 1) % cards.length;
        else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') next = (idx - 1 + cards.length) % cards.length;
        else if (e.key === 'Home') next = 0;
        else if (e.key === 'End') next = cards.length - 1;
        if (next === null) return;
        e.preventDefault();
        select(next, true);
    });

    /* Roving tabindex baseline: only the selected card is
       in the tab order */
    cards.forEach(function (c) {
        c.tabIndex = c.classList.contains('is-selected') ? 0 : -1;
    });
})();
