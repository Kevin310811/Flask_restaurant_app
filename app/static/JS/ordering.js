function showSidebar() {
    const sidebar = document.querySelector(`.sidebar`);
    sidebar.style.display = 'flex';
}

function hideSidebar() {
    const sidebar = document.querySelector(`.sidebar`);
    sidebar.style.display = 'none';
}

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

// Food items
const food = [
    // Sabjis
    { title: "Butter Chicken", desc: "Tandoor-roasted chicken in a creamy tomato-butter gravy. Rich, smooth, and mildly spiced.", type: "non-veg", flavour: "non-spicy", category: "sabji", id: 1, qty: 0, image: "Images/alex-munsell-Yr4n8O_3UPc-unsplash.jpg", price: 495 },
    { title: "Chicken Chettinand", desc: "South Indian chicken curry with black pepper, curry leaves, and roasted spices. Bold and spicy.", type: "non-veg", flavour: "spicy", category: "sabji", id: 2, qty: 0, image: "Images/davide-cantelli-jpkfc5_d-DI-unsplash.jpg", price: 485 },
    { title: "Lamb Rogan Josh", desc: "Slow-cooked lamb in a deep red Kashmiri gravy. Aromatic with balanced heat.", type: "non-veg", flavour: "spicy", category: "sabji", id: 3, qty: 0, image: "Images/lily-banse--YHSwy6uqvk-unsplash.jpg", price: 575 },
    { title: "Mutton Korma", desc: "Mutton braised in a mild yogurt and nut-based gravy. Fragrant and creamy.", type: "non-veg", flavour: "non-spicy", category: "sabji", id: 4, qty: 0, image: "Images/anh-nguyen-kcA-c3f_3FE-unsplash.jpg", price: 565 },
    { title: "Fish Moilee", desc: "Fish gently cooked in coconut milk with subtle spices and curry leaves. Light and delicate.", type: "non-veg", flavour: "non-spicy", category: "sabji", id: 5, qty: 0, image: "Images/alex-munsell-Yr4n8O_3UPc-unsplash.jpg", price: 525 },
    { title: "Prawn Masala", desc: "Prawns simmered in a thick onion-tomato masala. Tangy with moderate heat.", type: "non-veg", flavour: "spicy", category: "sabji", id: 6, qty: 0, image: "Images/davide-cantelli-jpkfc5_d-DI-unsplash.jpg", price: 595 },
    { title: "Chicken Tikka Masala", desc: "Grilled chicken in a spiced tomato gravy. Smoky and flavorful with medium heat.", type: "non-veg", flavour: "spicy", category: "sabji", id: 7, qty: 0, image: "Images/davide-cantelli-jpkfc5_d-DI-unsplash.jpg", price: 495 },
    { title: "Egg Curry", desc: "Boiled eggs in a robust onion-tomato curry. Hearty and moderately spicy.", type: "non-veg", flavour: "spicy", category: "sabji", id: 8, qty: 0, image: "Images/lily-banse--YHSwy6uqvk-unsplash.jpg", price: 365 },
    { title: "Goan Fish Curry", desc: "Fish cooked in a tangy coconut and tamarind sauce. Bright, coastal, and spicy.", type: "non-veg", flavour: "spicy", category: "sabji", id: 9, qty: 0, image: "Images/anh-nguyen-kcA-c3f_3FE-unsplash.jpg", price: 545 },
    { title: "Paneer Makhani", desc: "Cottage cheese simmered in a creamy tomato-butter gravy, mildly sweet and delicately spiced.", type: "veg", flavour: "non-spicy", category: "sabji", id: 10, qty: 0, image: "Images/alex-munsell-Yr4n8O_3UPc-unsplash.jpg", price: 395 },
    { title: "Kadai Paneer", desc: "Paneer with bell peppers in a bold, freshly ground kadai masala. Aromatic and moderately spicy.", type: "veg", flavour: "spicy", category: "sabji", id: 11, qty: 0, image: "Images/davide-cantelli-jpkfc5_d-DI-unsplash.jpg", price: 385 },
    { title: "Aloo Gobi", desc: "Potatoes and cauliflower sautéed with cumin and turmeric, lightly crisped with warming spices.", type: "veg", flavour: "spicy", category: "sabji", id: 12, qty: 0, image: "Images/lily-banse--YHSwy6uqvk-unsplash.jpg", price: 325 },
    { title: "Dal Tadka", desc: "Slow-cooked yellow lentils tempered with ghee, cumin, and garlic. Smooth and comforting.", type: "veg", flavour: "non-spicy", category: "sabji", id: 13, qty: 0, image: "Images/anh-nguyen-kcA-c3f_3FE-unsplash.jpg", price: 295 },
    { title: "Bhindi Masala", desc: "Okra sautéed with onions and tomatoes in a spiced masala base. Slightly tangy with medium heat.", type: "veg", flavour: "spicy", category: "sabji", id: 14, qty: 0, image: "Images/alex-munsell-Yr4n8O_3UPc-unsplash.jpg", price: 345 },
    { title: "Malai Kofta", desc: "Soft paneer-vegetable dumplings in a rich, creamy cashew-tomato sauce. Mild and indulgent.", type: "veg", flavour: "non-spicy", category: "sabji", id: 15, qty: 0, image: "Images/davide-cantelli-jpkfc5_d-DI-unsplash.jpg", price: 425 },
    { title: "Palak Paneer", desc: "Spinach purée cooked with gentle spices and tender paneer cubes. Smooth and earthy.", type: "veg", flavour: "non-spicy", category: "sabji", id: 16, qty: 0, image: "Images/lily-banse--YHSwy6uqvk-unsplash.jpg", price: 375 },
    { title: "Baingan Bharta", desc: "Fire-roasted eggplant mashed and cooked with onions and green chilies. Smoky and bold.", type: "veg", flavour: "spicy", category: "sabji", id: 17, qty: 0, image: "Images/anh-nguyen-kcA-c3f_3FE-unsplash.jpg", price: 335 },
    { title: "Methi Malai Mutter", desc: "Fenugreek leaves and peas in a light cream sauce. Mild with a delicate hint of bitterness.", type: "veg", flavour: "non-spicy", category: "sabji", id: 18, qty: 0, image: "Images/alex-munsell-Yr4n8O_3UPc-unsplash.jpg", price: 365 },

    // Indian Bread
    { title: "Tandoori Roti", desc: "Whole wheat flatbread baked in a traditional clay tandoor. Light, wholesome, and perfect to scoop up curries.", flavour: "non-spicy", category: "bread", id: 19, qty: 0, image: "Images/usman-yousaf-4GDW-Rt4BVQ-unsplash.jpg", price: 65 },
    { title: "Butter Roti", desc: "Tandoori roti brushed with golden butter. Soft, warm, and subtly rich.", flavour: "non-spicy", category: "bread", id: 20, qty: 0, image: "Images/usman-yousaf-4GDW-Rt4BVQ-unsplash.jpg", price: 65 },
    { title: "Plain Naan", desc: "Leavened soft bread baked in a clay oven. Slightly crisp on the outside, pillowy inside.", flavour: "non-spicy", category: "bread", id: 21, qty: 0, image: "Images/ajeet-panesar-WrE3ruckrwI-unsplash.jpg", price: 65 },
    { title: "Butter Naan", desc: "Classic naan topped with melted butter. Rich, fragrant, and indulgent with every bite.", flavour: "non-spicy", category: "bread", id: 22, qty: 0, image: "Images/ajeet-panesar-WrE3ruckrwI-unsplash.jpg", price: 65 },
    { title: "Garlic Naan", desc: "Naan infused with fresh garlic and coriander. Aromatic, flavorful, and perfect for spiced gravies.", flavour: "non-spicy", category: "bread", id: 23, qty: 0, image: "Images/ajeet-panesar-WrE3ruckrwI-unsplash.jpg", price: 65 },
    { title: "Roomali Roti", desc: "Ultra-thin, hand-stretched bread cooked on a convex griddle. Light, soft, and delicately textured.", flavour: "non-spicy", category: "bread", id: 24, qty: 0, image: "Images/usman-yousaf-4GDW-Rt4BVQ-unsplash.jpg", price: 65 },

    // Drinks
    { title: "Mango Lassi", desc: "Refreshing mango yogurt drink.", flavour: "non-spicy", category: "drink", id: 25, qty: 0, image: "Images/lassi.jpg", price: 120 },
    { title: "Masala Chai", desc: "Traditional spiced tea.", flavour: "non-spicy", category: "drink", id: 26, qty: 0, image: "Images/chai.jpg", price: 80 },

    // Desserts
    { title: "Gulab Jamun", desc: "Soft syrup-soaked milk dumplings.", flavour: "non-spicy", category: "dessert", id: 27, qty: 0, image: "Images/gulabjamun.jpg", price: 150 },
    { title: "Rasgulla", desc: "Spongy syrupy dessert balls.", flavour: "non-spicy", category: "dessert", id: 28, qty: 0, image: "Images/rasgulla.jpg", price: 140 },
];

// Restore cart from localStorage if coming back from payment page
const pendingOrder = JSON.parse(localStorage.getItem('pendingOrder'));
if (pendingOrder) {
    pendingOrder.items.forEach(savedItem => {
        const match = food.find(f => f.id === savedItem.id);
        if (match) match.qty = savedItem.qty;
    });
    localStorage.removeItem('pendingOrder');
}

function getSelectedCategory() {
    const tmp = document.querySelector('input[name="food"]:checked');
    return tmp ? tmp.value : '';
}

function filterFood() {
    const category = getSelectedCategory();

    const disableFilters = (category !== "sabji");
    veg.disabled = non_veg.disabled = spicy.disabled = non_spicy.disabled = disableFilters;

    return food.filter(item => {
        if (item.category !== category) return false;

        if (category === "sabji") {
            if (veg.checked !== non_veg.checked) {
                if (veg.checked && item.type !== "veg") return false;
                if (non_veg.checked && item.type !== "non-veg") return false;
            }
            if (spicy.checked !== non_spicy.checked) {
                if (spicy.checked && item.flavour !== "spicy") return false;
                if (non_spicy.checked && item.flavour !== "non-spicy") return false;
            }
        }

        return true;
    });
}

function updateItemCount() {
    const totalItems = food.reduce((total, item) => total + item.qty, 0);
    document.getElementById("item-count").textContent = `Items selected: ${totalItems}`;
}

function display_food() {
    const food_listing = document.getElementById("food-listing");
    food_listing.innerHTML = "";

    const filtered_results = filterFood();

    filtered_results.forEach(item => {
        const card = document.createElement("div");
        card.className = "item";
        card.innerHTML = `
            <img src="${item.image}" alt="">
            <div class="item-text">
                <h1>${item.title}</h1>
                <p>${item.desc}</p>
                <p class="price">₹${item.price}</p>
                <div class="qty-btn">
                    <button class="decrease">-</button>
                    <p class="count">${item.qty}</p>
                    <button class="increase">+</button>
                </div>
            </div>
        `;

        food_listing.append(card);

        const decreaseBtn = card.querySelector(".decrease");
        const increaseBtn = card.querySelector(".increase");
        const countLabel = card.querySelector(".count");

        increaseBtn.addEventListener("click", () => {
            if (item.qty < 20) {
                item.qty++;
                countLabel.textContent = item.qty;
                updateItemCount();
                updateCart();
            }
        });

        decreaseBtn.addEventListener("click", () => {
            if (item.qty > 0) {
                item.qty--;
                countLabel.textContent = item.qty;
                updateItemCount();
                updateCart();
            }
        });
    });
}

function updateCart() {
    const cartList = document.getElementById("cart-items");
    const cartTotal = document.getElementById("cart-total");
    if (!cartList || !cartTotal) return;

    cartList.innerHTML = "";

    const cartItems = food.filter(item => item.qty > 0);

    cartItems.forEach(item => {
        const li = document.createElement("li");
        const subtotal = (item.qty * item.price).toFixed(2);

        li.innerHTML = `
            <span class="cart-title">${item.title}</span>
            <div class="cart-controls">
                <button class="cart-decrease">-</button>
                <span class="cart-qty">${item.qty}</span>
                <button class="cart-increase">+</button>
            </div>
            <span class="cart-subtotal">₹${subtotal}</span>
        `;

        cartList.appendChild(li);

        const decreaseBtn = li.querySelector(".cart-decrease");
        const increaseBtn = li.querySelector(".cart-increase");
        const qtyLabel = li.querySelector(".cart-qty");

        increaseBtn.addEventListener("click", () => {
            if (item.qty < 20) {
                item.qty++;
                qtyLabel.textContent = item.qty;
                updateItemCount();
                updateCart();
                display_food();
            }
        });

        decreaseBtn.addEventListener("click", () => {
            if (item.qty > 0) {
                item.qty--;
                updateItemCount();
                updateCart();
                display_food();
            }
        });
    });

    const totalCost = cartItems.reduce((sum, item) => sum + item.qty * item.price, 0);
    cartTotal.textContent = `Total: ₹${totalCost.toFixed(2)}`;
}

veg.addEventListener("change", display_food);
non_veg.addEventListener("change", display_food);
spicy.addEventListener("change", display_food);
non_spicy.addEventListener("change", display_food);

sabjisRadio.addEventListener("change", display_food);
breadRadio.addEventListener("change", display_food);
drinksRadio.addEventListener("change", display_food);
dessertRadio.addEventListener("change", display_food);

display_food();
updateItemCount();
updateCart();

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
    const cartItems = food.filter(item => item.qty > 0);

    if (cartItems.length === 0) {
        emptyCartModal.classList.add("active");
        return;
    }

    modalItems.innerHTML = "";

    cartItems.forEach(item => {
        const li = document.createElement("li");
        li.innerHTML = `
            <span>${item.title} x${item.qty}</span>
            <span>₹${(item.qty * item.price).toFixed(2)}</span>
        `;
        modalItems.appendChild(li);
    });

    const totalCost = cartItems.reduce((sum, item) => sum + item.qty * item.price, 0);
    modalTotal.textContent = `Total: ₹${totalCost.toFixed(2)}`;

    modal.classList.add("active");
});

emptyCartClose.addEventListener("click", () => {
    emptyCartModal.classList.remove("active");
});

modalEdit.addEventListener("click", () => {
    modal.classList.remove("active");
});

modalPay.addEventListener("click", () => {
    const cartItems = food.filter(item => item.qty > 0);
    const totalCost = cartItems.reduce((sum, item) => sum + item.qty * item.price, 0);

    const orderData = {
        items: cartItems.map(item => ({
            id: item.id,
            title: item.title,
            qty: item.qty,
            price: item.price,
            subtotal: item.qty * item.price
        })),
        total: totalCost
    };

    localStorage.setItem("pendingOrder", JSON.stringify(orderData));

    food.forEach(item => item.qty = 0);
    updateItemCount();
    updateCart();
    display_food();
    modal.classList.remove("active");
    window.location.href = "payment.html";
});