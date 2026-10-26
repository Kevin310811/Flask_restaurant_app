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

    /* Body copy reuses the site's existing placeholder
       sentences verbatim — no new content is invented. */
    var LOREM_A = 'Lorem ipsum dolor sit amet consectetur adipisicing elit. Dolore accusantium optio quo corrupti, dicta eum odio illum sapiente, consequatur quibusdam officiis mollitia nobis?';
    var LOREM_B = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Ex nobis, molestiae temporibus ad deleniti, aliquam eius nam eos dolore nulla veniam incidunt eum optio sed. Delectus, debitis aliquid. Debitis, eum.';

    function plate(src, title, text) {
        return { src: src, title: title, text: text };
    }

    /* Decks drawn from existing project photography; titles
       simply describe what each photo shows. Bread, drink
       and sweet rotate through the columns like courses. */
    var DECKS = [
        [
            plate('/static/Images/ajeet-panesar-WrE3ruckrwI-unsplash.jpg', 'Fresh Naan', LOREM_A),
            plate('/static/Images/chai.jpg', 'Masala Chai', LOREM_B),
            plate('/static/Images/gulabjamun.jpg', 'Gulab Jamun', LOREM_A)
        ],
        [
            plate('/static/Images/alex-munsell-Yr4n8O_3UPc-unsplash.jpg', 'Seared & Glazed', LOREM_A),
            plate('/static/Images/yosuke-ota-lA3xO5pGctc-unsplash.jpg', 'Warm Naan', LOREM_B),
            plate('/static/Images/lassi.jpg', 'Mango Lassi', LOREM_A)
        ],
        [
            plate('/static/Images/lily-banse--YHSwy6uqvk-unsplash.jpg', 'Small Plates', LOREM_A),
            plate('/static/Images/rasgulla.jpg', 'Rasgulla', LOREM_B),
            plate('/static/Images/usman-yousaf-4GDW-Rt4BVQ-unsplash.jpg', 'Everyday Rotis', LOREM_A)
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
