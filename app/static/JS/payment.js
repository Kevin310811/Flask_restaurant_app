document.addEventListener('DOMContentLoaded', () => {
    const paymentTotal = document.getElementById('payment-total');
    const tipAmountLabel = document.getElementById('tip-amount');
    const customTipInput = document.getElementById('custom-tip');
    const payBtn = document.getElementById('pay-btn');

    let subtotal = parseFloat(payBtn.dataset.subtotal) || 0;
    let tipAmount = 0;

    function updateTotal() {
        const total = subtotal + tipAmount;
        tipAmountLabel.textContent = `₹${tipAmount.toFixed(2)}`;
        paymentTotal.textContent = `₹${total.toFixed(2)}`;
    }

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
        payBtn.disabled = true;

        try {
            const createRes = await fetch('/api/payment/create-order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({ tip: tipAmount })
            });
            const createData = await createRes.json();

            if (!createRes.ok) {
                alert(createData.error || 'Could not start payment. Please try again.');
                payBtn.disabled = false;
                return;
            }

            const options = {
                key: createData.key_id,
                amount: createData.amount,
                currency: 'INR',
                name: 'Restaurant',
                description: 'Food Order Payment',
                order_id: createData.order_id,
                handler: async function (response) {
                    const verifyRes = await fetch('/api/payment/verify', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCsrfToken()
                        },
                        body: JSON.stringify({
                            razorpay_order_id: response.razorpay_order_id,
                            razorpay_payment_id: response.razorpay_payment_id,
                            razorpay_signature: response.razorpay_signature,
                            tip: tipAmount
                        })
                    });
                    const verifyData = await verifyRes.json();

                    if (verifyData.success) {
                        window.location.href = '/';
                    } else {
                        alert('Payment could not be verified. If money was deducted, please contact support with payment ID: ' + response.razorpay_payment_id);
                    }
                },
                modal: {
                    ondismiss: function () {
                        payBtn.disabled = false;
                    }
                },
                theme: {
                    color: '#f5c542'
                }
            };

            const rzp = new Razorpay(options);
            rzp.open();
        } catch (err) {
            alert('Something went wrong. Please try again.');
            payBtn.disabled = false;
        }
    });
});