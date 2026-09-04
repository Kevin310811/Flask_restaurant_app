document.addEventListener('DOMContentLoaded', () => {
    const paymentTotal = document.getElementById('payment-total');
    const tipAmountLabel = document.getElementById('tip-amount');
    const customTipInput = document.getElementById('custom-tip');
    const payBtn = document.getElementById('pay-btn');

    // Subtotal is passed from Flask via data attribute
    let subtotal = parseFloat(payBtn.dataset.subtotal) || 0;
    let tipAmount = 0;

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

    payBtn.addEventListener('click', async () => {
        const total = subtotal + tipAmount;

        const res = await fetch('/api/checkout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ tip: tipAmount })
        });

        const data = await res.json();

        if (data.success) {
            const totalPaise = Math.round(total * 100);

            const options = {
                key: 'rzp_test_SOlJlNIHn1YXG9',
                amount: totalPaise,
                currency: 'INR',
                name: 'Restaurant',
                description: 'Food Order Payment',
                handler: function(response) {
                    alert('Payment Successful! Payment ID: ' + response.razorpay_payment_id);
                    window.location.href = '/';
                },
                theme: {
                    color: '#f5c542'
                }
            };

            const rzp = new Razorpay(options);
            rzp.open();
        } else {
            alert('Something went wrong. Please try again.');
        }
    });
});