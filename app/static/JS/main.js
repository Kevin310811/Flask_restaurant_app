function showSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.style.display = 'flex';
}

function hideSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.style.display = 'none';
}

const form = document.getElementById('form');
if (form) {

    const timeInput = document.getElementById('time');

    function formatDateForInput(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        return `${year}-${month}-${day}T${hours}:${minutes}`;
    }

    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(8, 30, 0, 0);

    const maxDate = new Date();
    maxDate.setDate(maxDate.getDate() + 31);
    maxDate.setHours(23, 0, 0, 0);

    timeInput.min = formatDateForInput(tomorrow);
    timeInput.max = formatDateForInput(maxDate);

    const blurFilter = document.querySelector('.blur-filter');
    const reservationsContainer = document.getElementById('reservations');
    const hasReservation = document.getElementById('has-reservation');

    form.addEventListener('submit', (e) => {
        e.preventDefault();

        const firstName = document.getElementById('firstName').value.trim();
        const lastName = document.getElementById('lastName').value.trim();
        const phoneNumber = document.getElementById('phoneNumber').value.trim();
        const numberOfPeople = document.getElementById('numberOfPeople').value;
        const timeValue = document.getElementById('time').value;
        const emailAddress = document.getElementById('email').value.trim();

        if (!timeValue) {
            alert('Please select a date and time.');
            return;
        }

        const selectedTime = new Date(timeValue);
        const totalMinutes = selectedTime.getHours() * 60 + selectedTime.getMinutes();

        if (totalMinutes < 8 * 60 + 30 || totalMinutes > 23 * 60) {
            alert('Please select a time between 8:30 AM and 11:00 PM.');
            return;
        }

        // Preview snapped time in modal
        const snappedMinutes = Math.floor(selectedTime.getMinutes() / 15) * 15;
        const snappedTime = new Date(selectedTime);
        snappedTime.setMinutes(snappedMinutes, 0, 0);

        const formattedDate = snappedTime.toLocaleString('en-IN', {
            dateStyle: 'medium',
            timeStyle: 'short'
        });

        blurFilter.style.visibility = 'visible';
        blurFilter.innerHTML = '';

        const modal = document.createElement('div');
        modal.className = 'card-modal';
        modal.innerHTML = `
            <h1 class="card-title">Reservation for ${firstName} ${lastName}</h1>
            <ul class="card-details">
                <li class="card-details-li">Time: ${formattedDate}</li>
                <li class="card-details-li">Phone Number: ${phoneNumber}</li>
                <li class="card-details-li">Number of people: ${numberOfPeople}</li>
                <li class="card-details-li">Email: ${emailAddress}</li>
            </ul>
            <p style="font-size:13px; opacity:0.7; margin-bottom:12px;">
                Your reservation will be snapped to the nearest 15-minute slot.
            </p>
            <button class="confirm-btn">Confirm</button>
            <button class="deny-btn">Cancel</button>
        `;

        blurFilter.appendChild(modal);

        modal.querySelector('.confirm-btn').addEventListener('click', async () => {
            const confirmBtn = modal.querySelector('.confirm-btn');
            confirmBtn.disabled = true;
            confirmBtn.textContent = 'Saving...';

            const res = await fetch('/reservations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    first_name: firstName,
                    last_name: lastName,
                    phone: phoneNumber,
                    people: parseInt(numberOfPeople),
                    time: timeValue,
                    email: emailAddress
                })
            });

            const data = await res.json();

            if (data.success) {
                const r = data.reservation;

                // Append new card to DOM
                const card = document.createElement('div');
                card.className = 'reservation-card';
                card.innerHTML = `
                    <h1 class="card-title">Reservation for ${r.first_name} ${r.last_name}</h1>
                    <ul class="card-details">
                        <li class="card-details-li">Time: ${r.slot_time}</li>
                        <li class="card-details-li">Phone: ${r.phone}</li>
                        <li class="card-details-li">People: ${r.people}</li>
                        <li class="card-details-li">Email: ${r.email}</li>
                    </ul>
                `;

                if (hasReservation) hasReservation.style.display = 'none';
                reservationsContainer.appendChild(card);

                blurFilter.style.visibility = 'hidden';
                blurFilter.innerHTML = '';
                form.reset();
            } else {
                confirmBtn.disabled = false;
                confirmBtn.textContent = 'Confirm';
                const existing = modal.querySelector('.error-msg');
                if (existing) existing.remove();
                const errMsg = document.createElement('p');
                errMsg.className = 'error-msg';
                errMsg.style.cssText = 'color: #ff6b6b; font-size:14px; margin-top:10px;';
                errMsg.textContent = data.error;
                modal.appendChild(errMsg);
            }
        });

        modal.querySelector('.deny-btn').addEventListener('click', () => {
            blurFilter.style.visibility = 'hidden';
            blurFilter.innerHTML = '';
        });
    });
}