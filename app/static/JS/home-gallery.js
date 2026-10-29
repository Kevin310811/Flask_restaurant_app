/* =====================================================
   HOMEPAGE — gallery-wall rotator
   -----------------------------------------------------
   The three plates re-hang every 3 seconds: each card
   cycles a small deck of photo + title + text pairs.
   The first plate of each deck is rendered in plain
   HTML, so the gallery still works without JavaScript.
   Hovering a card pauses its rotation; background tabs
   idle. All photography already ships in static/Images.
   ===================================================== */
(function () {
    'use strict';

    var INTERVAL = 3000;  /* user-requested: a new plate every 3s */
    var OUT_MS = 380;     /* wipe-out duration before each swap */
    var LOAD_CAP = 1200;  /* never hold a swap waiting on a slow fetch */

    /* Captions describe what each photograph actually shows.
       Dish images reuse the site's existing gallery captions
       verbatim where they exist — no new content is invented. */
    function plate(src, title, text) {
        return { src: src, title: title, text: text };
    }

    /* Decks drawn from project photography; titles describe
       what each photo shows. Bread, drink and sweet rotate
       through every column like courses. Sources are the
       web-sized copies in Images/opt (originals stay for
       the gallery page and menu thumbnails). */
    var DECKS = [
        [
            plate('/static/Images/opt/ajeet-panesar-WrE3ruckrwI-unsplash.jpg', 'Fresh Naan', 'Blistered naan, straight off the griddle.'),
            plate('/static/Images/opt/chai.jpg', 'Masala Chai', 'A warm cup of masala chai to start your day.'),
            plate('/static/Images/opt/gulabjamun.jpg', 'Gulab Jamun', 'Soft gulab jamun soaked in rose syrup.')
        ],
        [
            plate('/static/Images/opt/alex-munsell-Yr4n8O_3UPc-unsplash.jpg', 'Seared & Glazed', 'Glazed from the pan, finished with bright greens.'),
            plate('/static/Images/opt/yosuke-ota-lA3xO5pGctc-unsplash.jpg', 'Warm Naan', 'Pillow-soft, straight from the basket.'),
            plate('/static/Images/opt/lassi.jpg', 'Mango Lassi', 'Refreshing mango lassi, made fresh daily.')
        ],
        [
            plate('/static/Images/opt/lily-banse--YHSwy6uqvk-unsplash.jpg', 'Small Plates', 'Three small plates, one long table.'),
            plate('/static/Images/opt/rasgulla.jpg', 'Rasgulla', 'Light and spongy rasgulla, a Bengali classic.'),
            plate('/static/Images/opt/usman-yousaf-4GDW-Rt4BVQ-unsplash.jpg', 'Everyday Rotis', 'A clean stack of everyday rotis.')
        ]
    ];

    var cards = document.querySelectorAll('.food-gallery .card[data-rotator]');
    if (!cards.length) return;

    var REDUCED = window.matchMedia
        && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    /* Resolve as soon as the photo is cached, or at the cap —
       a swap may then pop in, but never stalls the rhythm. */
    function preload(src) {
        return new Promise(function (resolve) {
            var img = new Image();
            var settled = false;
            function finish() {
                if (!settled) { settled = true; resolve(); }
            }
            img.onload = finish;
            img.onerror = finish;
            img.src = src;
            window.setTimeout(finish, LOAD_CAP);
        });
    }

    function initCard(card, deck) {
        var img = card.querySelector('img');
        var title = card.querySelector('.card-content > h1');
        var body = card.querySelector('.card-content > p');
        var index = 0;
        var busy = false;
        var paused = false;

        /* Keep the following plate warm so swaps stay seamless */
        function warm(upcoming) {
            preload(deck[upcoming].src);
        }

        function apply(next) {
            img.src = deck[next].src;
            title.textContent = deck[next].title;
            body.textContent = deck[next].text;
            warm((next + 1) % deck.length);
        }

        function swap() {
            var next = (index + 1) % deck.length;
            busy = true;
            preload(deck[next].src).then(function () {
                var outMs = REDUCED ? 0 : OUT_MS;
                card.classList.add('is-out');
                window.setTimeout(function () {
                    apply(next);
                    index = next;
                    card.classList.remove('is-out');
                    busy = false;
                }, outMs);
            });
        }

        window.setInterval(function () {
            if (busy || paused || document.hidden) return;
            swap();
        }, INTERVAL);

        card.addEventListener('mouseenter', function () { paused = true; });
        card.addEventListener('mouseleave', function () { paused = false; });

        /* Manual advance — used by tests and debugging */
        card.plateAdvance = swap;

        /* Warm the first upcoming photo after load so the
           opening swap at t=3s is seamless */
        window.addEventListener('load', function () {
            window.setTimeout(function () { warm((index + 1) % deck.length); }, 1500);
        });
    }

    Array.prototype.forEach.call(cards, function (card, i) {
        initCard(card, DECKS[i]);
    });
})();
