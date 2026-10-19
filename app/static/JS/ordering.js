// Filters
const veg = document.getElementById("veg");
const non_veg = document.getElementById("non-veg");
const spicy = document.getElementById("spicy");
const non_spicy = document.getElementById("non-spicy");

// Category radios
const sabjisRadio = document.getElementById("sabjis");
const breadRadio = document.getElementById("bread");
const drinksRadio = document.getElementById("drinks");
const dessertRadio = document.getElementById("dessert");

// Local state — fetched from Flask API
let foodItems = [];
let cartState = { items: [], total: 0 };

// Fetch menu from Flask
async function fetchMenu() {
    const category = getSelectedCategory();
    const params = new URLSearchParams({ category });

    if (category === 'sabji') {
        if (veg.checked && !non_veg.checked) params.append('type', 'veg');
        if (non_veg.checked && !veg.checked) params.append('type', 'non-veg');
        if (spicy.checked && !non_spicy.checked) params.append('flavour', 'spicy');
        if (non_spicy.checked && !spicy.checked) params.append('flavour', 'non-spicy');
    }

    const res = await fetch(`/api/menu?${params.toString()}`);

    if (res.status === 401 || res.redirected) {
        window.location.href = '/login';
        return;
    }

    foodItems = await res.json();
    display_food();
}

// Fetch cart from Flask
async function fetchCart() {
    const res = await fetch('/api/cart');
    cartState = await res.json();
    updateCart();
    updateItemCount();
}

// Update qty on server. Returns true if the server accepted the change.
async function updateQty(menuItemId, qty) {
    let res, data;
    try {
        res = await fetch('/api/cart/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ menu_item_id: menuItemId, qty })
        });
        data = await res.json();
    } catch (err) {
        // Network failure, or a non-JSON response (e.g. an expired
        // session redirecting to the login page).
        alert('Could not update your cart. Please refresh the page and try again.');
        return false;
    }

    // The server answers with {"error": ...} when it rejects a change
    // (item sold out, quantity over the cap, ...). Previously that body
    // was assigned straight to cartState, which broke every later
    // cartState.items call. Now we show the message and resync instead.
    if (!res.ok) {
        alert(data.error || 'Could not update your cart. Please try again.');
        await fetchCart();
        await fetchMenu();
        return false;
    }

    cartState = data;
    updateCart();
    updateItemCount();
    display_food();
    return true;
}

function getSelectedCategory() {
    const tmp = document.querySelector('input[name="food"]:checked');
    return tmp ? tmp.value : 'sabji';
}

function getCartQty(itemId) {
    const found = cartState.items.find(i => i.menu_item_id === itemId);
    return found ? found.qty : 0;
}

function updateItemCount() {
    const totalItems = cartState.items.reduce((sum, i) => sum + i.qty, 0);
    document.getElementById("item-count").textContent = `Items selected: ${totalItems}`;
}

function display_food() {
    const food_listing = document.getElementById("food-listing");
    food_listing.innerHTML = "";

    const disableFilters = (getSelectedCategory() !== "sabji");
    veg.disabled = non_veg.disabled = spicy.disabled = non_spicy.disabled = disableFilters;

    foodItems.forEach(item => {
        const qty = getCartQty(item.id);
        const soldOut = !item.is_available;
        const hasDiscount = item.discount_percent > 0;

        // Match the cart/checkout, which already charge the discounted price.
        const priceHtml = hasDiscount
            ? `<span class="price-original">₹${item.price}</span> ₹${item.discounted_price.toFixed(2)} <span class="price-discount">${item.discount_percent}% off</span>`
            : `₹${item.price}`;

        const card = document.createElement("div");
        card.className = soldOut ? "item sold-out" : "item";
        card.innerHTML = `
            <div class="item-image" style="background-image: url('/static/${item.image}')">
                <div class="item-image-overlay">
                    <p class="item-image-category">${item.category.toUpperCase()}</p>
                    ${item.type ? `<p class="item-image-type ${item.type}">${item.type}</p>` : ''}
                    ${soldOut ? `<p class="item-sold-out-badge">SOLD OUT</p>` : ''}
                </div>
            </div>
            <div class="item-text">
                <h1>${item.title}</h1>
                <p>${item.desc}</p>
                <p class="price">${priceHtml}</p>
                <div class="qty-btn">
                    <button class="decrease">-</button>
                    <p class="count">${qty}</p>
                    <button class="increase" ${soldOut ? 'disabled' : ''}>+</button>
                </div>
            </div>
        `;

        food_listing.append(card);

        const decreaseBtn = card.querySelector(".decrease");
        const increaseBtn = card.querySelector(".increase");
        const countLabel = card.querySelector(".count");

        // The decrease button stays enabled on sold-out items so someone
        // who already added one can still take it out of their cart.
        increaseBtn.addEventListener("click", async () => {
            if (soldOut) return;
            const currentQty = getCartQty(item.id);
            if (currentQty < 20) {
                await updateQty(item.id, currentQty + 1);
                countLabel.textContent = getCartQty(item.id);
            }
        });

        decreaseBtn.addEventListener("click", async () => {
            const currentQty = getCartQty(item.id);
            if (currentQty > 0) {
                await updateQty(item.id, currentQty - 1);
                countLabel.textContent = getCartQty(item.id);
            }
        });
    });
}

function updateCart() {
    const cartList = document.getElementById("cart-items");
    const cartTotal = document.getElementById("cart-total");
    if (!cartList || !cartTotal) return;

    cartList.innerHTML = "";

    cartState.items.forEach(item => {
        const li = document.createElement("li");
        li.innerHTML = `
            <span class="cart-title">${item.title}</span>
            <div class="cart-controls">
                <button class="cart-decrease" data-id="${item.menu_item_id}">-</button>
                <span class="cart-qty">${item.qty}</span>
                <button class="cart-increase" data-id="${item.menu_item_id}">+</button>
            </div>
            <span class="cart-subtotal">₹${item.subtotal.toFixed(2)}</span>
        `;
        cartList.appendChild(li);

        li.querySelector(".cart-increase").addEventListener("click", async () => {
            if (item.qty < 20) await updateQty(item.menu_item_id, item.qty + 1);
        });

        li.querySelector(".cart-decrease").addEventListener("click", async () => {
            if (item.qty > 0) await updateQty(item.menu_item_id, item.qty - 1);
        });
    });

    cartTotal.textContent = `Total: ₹${cartState.total.toFixed(2)}`;
}

// Filter/category listeners
veg.addEventListener("change", fetchMenu);
non_veg.addEventListener("change", fetchMenu);
spicy.addEventListener("change", fetchMenu);
non_spicy.addEventListener("change", fetchMenu);

sabjisRadio.addEventListener("change", fetchMenu);
breadRadio.addEventListener("change", fetchMenu);
drinksRadio.addEventListener("change", fetchMenu);
dessertRadio.addEventListener("change", fetchMenu);

// Modals
const modal = document.getElementById("bill-modal");
const modalItems = document.getElementById("modal-items");
const modalTotal = document.getElementById("modal-total");
const modalEdit = document.getElementById("modal-edit");
const modalPay = document.getElementById("modal-pay");
const emptyCartModal = document.getElementById("empty-cart-modal");
const emptyCartClose = document.getElementById("empty-cart-close");
const checkoutBtn = document.getElementById("checkout-btn");

checkoutBtn.addEventListener("click", () => {
    if (cartState.items.length === 0) {
        emptyCartModal.classList.add("active");
        return;
    }

    modalItems.innerHTML = "";
    cartState.items.forEach(item => {
        const li = document.createElement("li");
        li.innerHTML = `
            <span>${item.title} x${item.qty}</span>
            <span>₹${item.subtotal.toFixed(2)}</span>
        `;
        modalItems.appendChild(li);
    });

    modalTotal.textContent = `Total: ₹${cartState.total.toFixed(2)}`;
    modal.classList.add("active");
});

emptyCartClose.addEventListener("click", () => {
    emptyCartModal.classList.remove("active");
});

modalEdit.addEventListener("click", () => {
    modal.classList.remove("active");
});

modalPay.addEventListener("click", () => {
    window.location.href = '/payment';
});

// Init
fetchCart();
fetchMenu();