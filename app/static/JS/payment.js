function showSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.style.display = 'flex';
}

function hideSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.style.display = 'none';
}

document.addEventListener('DOMContentLoaded', () => {
    const orderData = JSON.parse(localStorage.getItem('pendingOrder'));

    if (!orderData || !orderData.items || orderData.items.length === 0) {
        document.querySelector('.payment-page').innerHTML = `
            <div class="payment-box">
                <h2 class="payment-title">No Order Found</h2>
                <p style="font-size:18px; margin-bottom:16px;">You have no active order.</p>
                <button onclick="window.location.href='order.html'" style="padding:10px; font-size:18px; border:1px solid white; border-radius:8px; background:black; color:white; width:100%; cursor:pointer; font-family:Inter, sans-serif;">
                    Go to Menu
                </button>
            </div>
        `;
        return;
    }

    const paymentItems = document.getElementById('payment-items');
    const paymentSubtotal = document.getElementById('payment-subtotal');
    const paymentTotal = document.getElementById('payment-total');
    const tipAmountLabel = document.getElementById('tip-amount');
    const customTipInput = document.getElementById('custom-tip');

    let subtotal = 0;
    let tipAmount = 0;

    orderData.items.forEach(item => {
        const li = document.createElement('li');
        li.innerHTML = `
            <span>${item.title} x${item.qty}</span>
            <span>₹${item.subtotal.toFixed(2)}</span>
        `;
        paymentItems.appendChild(li);
    });

    subtotal = orderData.total;
    paymentSubtotal.textContent = `₹${subtotal.toFixed(2)}`;
    updateTotal();

    function updateTotal() {
        const total = subtotal + tipAmount;
        tipAmountLabel.textContent = `₹${tipAmount.toFixed(2)}`;
        paymentTotal.textContent = `₹${total.toFixed(2)}`;
    }

    // Tip preset buttons
    const tipBtns = document.querySelectorAll('.tip-btn');

    tipBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tipBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            customTipInput.value = '';
            const percent = parseFloat(btn.dataset.percent);
            tipAmount = (subtotal * percent) / 100;
            updateTotal();
        });
    });

    customTipInput.addEventListener('input', () => {
        tipBtns.forEach(b => b.classList.remove('active'));
        tipAmount = parseFloat(customTipInput.value) || 0;
        updateTotal();
    });

    document.getElementById('edit-order-btn').addEventListener('click', () => {
        window.location.href = 'order.html';
    });

    document.getElementById('pay-btn').addEventListener('click', () => {
        const total = subtotal + tipAmount;
        const totalPaise = Math.round(total * 100);

        const options = {
            key: 'rzp_test_SOlJlNIHn1YXG9',
            amount: totalPaise,
            currency: 'INR',
            name: 'Restaurant',
            description: 'Food Order Payment',
            handler: function(response) {
                localStorage.removeItem('pendingOrder');
                alert('Payment Successful! Payment ID: ' + response.razorpay_payment_id);
                window.location.href = 'index.html';
            },
            theme: {
                color: '#f5c542'
            }
        };

        const rzp = new Razorpay(options);
        rzp.open();
    });
});