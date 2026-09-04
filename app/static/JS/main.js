// Reads the CSRF token Flask-WTF renders into <meta name="csrf-token">
// in base.html. Every JS file that POSTs JSON (this file, ordering.js,
// payment.js) calls this and sends the result as the X-CSRFToken
// header, since CSRFProtect can't read a token from a JSON body the
// way it reads one from a form field.
function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]').content;
}

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

    const blurFilter = document.querySelector('.blur-filter');
    const reservationsContainer = document.getElementById('reservations');
    const hasReservation = document.getElementById('has-reservation');

    // --- Date & Slot Picker ---
    const dateInput = document.getElementById('slot-date-input');
    const dateLabel = document.getElementById('slot-date-label');
    const prevDayBtn = document.getElementById('prev-day');
    const nextDayBtn = document.getElementById('next-day');
    const slotGrid = document.getElementById('slot-grid');
    const slotSelected = document.getElementById('slot-selected');
    const slotSelectedLabel = document.getElementById('slot-selected-label');
    const btnAM = document.getElementById('btn-am');
    const btnPM = document.getElementById('btn-pm');

    let selectedDate = null;
    let selectedPeriod = 'AM';
    let selectedSlot = null;

    // Set min date to tomorrow
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const maxDate = new Date();
    maxDate.setDate(maxDate.getDate() + 31);

    function formatDateISO(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    function formatDateDisplay(date) {
        return date.toLocaleDateString('en-IN', {
            weekday: 'short',
            day: 'numeric',
            month: 'short',
            year: 'numeric'
        });
    }

    dateInput.min = formatDateISO(tomorrow);
    dateInput.max = formatDateISO(maxDate);

    function setDate(date) {
        if (date < tomorrow || date > maxDate) return;
        selectedDate = date;
        dateInput.value = formatDateISO(date);
        dateLabel.textContent = formatDateDisplay(date);
        selectedSlot = null;
        slotSelected.style.display = 'none';
        fetchSlots();
    }

    dateInput.addEventListener('change', () => {
        const parts = dateInput.value.split('-');
        const picked = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]));
        setDate(picked);
    });

    prevDayBtn.addEventListener('click', () => {
        if (!selectedDate) return;
        const prev = new Date(selectedDate);
        prev.setDate(prev.getDate() - 1);
        setDate(prev);
    });

    nextDayBtn.addEventListener('click', () => {
        if (!selectedDate) {
            setDate(new Date(tomorrow));
        } else {
            const next = new Date(selectedDate);
            next.setDate(next.getDate() + 1);
            setDate(next);
        }
    });

    btnAM.addEventListener('click', () => {
        selectedPeriod = 'AM';
        btnAM.classList.add('active');
        btnPM.classList.remove('active');
        selectedSlot = null;
        slotSelected.style.display = 'none';
        if (selectedDate) fetchSlots();
    });

    btnPM.addEventListener('click', () => {
        selectedPeriod = 'PM';
        btnPM.classList.add('active');
        btnAM.classList.remove('active');
        selectedSlot = null;
        slotSelected.style.display = 'none';
        if (selectedDate) fetchSlots();
    });

    async function fetchSlots() {
        slotGrid.innerHTML = '<p class="slot-placeholder">Loading slots...</p>';
        const dateStr = formatDateISO(selectedDate);
        const res = await fetch(`/api/slots?date=${dateStr}&period=${selectedPeriod}`);
        const slots = await res.json();
        renderSlots(slots);
    }

    function renderSlots(slots) {
        slotGrid.innerHTML = '';

        if (slots.length === 0) {
            slotGrid.innerHTML = '<p class="slot-placeholder">No slots available for this period.</p>';
            return;
        }

        slots.forEach(slot => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'slot-btn' + (slot.available ? '' : ' unavailable');
            btn.textContent = slot.display;
            btn.dataset.time = slot.time;
            btn.dataset.display = slot.display;
            btn.title = slot.available
                ? `${slot.spots_left} spots left`
                : 'Fully booked';

            if (!slot.available) {
                btn.disabled = true;
            } else {
                btn.addEventListener('click', () => {
                    document.querySelectorAll('.slot-btn').forEach(b => b.classList.remove('selected'));
                    btn.classList.add('selected');
                    selectedSlot = slot.time;
                    slotSelectedLabel.textContent = slot.display;
                    slotSelected.style.display = 'block';
                });
            }

            slotGrid.appendChild(btn);
        });
    }

    // --- Form Submit ---
    form.addEventListener('submit', (e) => {
        e.preventDefault();

        const firstName = document.getElementById('firstName').value.trim();
        const lastName = document.getElementById('lastName').value.trim();
        const phoneNumber = document.getElementById('phoneNumber').value.trim();
        const numberOfPeople = document.getElementById('numberOfPeople').value;
        const emailAddress = document.getElementById('email').value.trim();

        if (!selectedDate) {
            alert('Please select a date.');
            return;
        }

        if (!selectedSlot) {
            alert('Please select a time slot.');
            return;
        }

        const dateStr = formatDateISO(selectedDate);
        const timeValue = `${dateStr}T${selectedSlot}`;

        blurFilter.style.visibility = 'visible';
        blurFilter.innerHTML = '';

        const modal = document.createElement('div');
        modal.className = 'card-modal';
        modal.innerHTML = `
            <h1 class="card-title">Reservation for ${firstName} ${lastName}</h1>
            <ul class="card-details">
                <li class="card-details-li">Date: ${formatDateDisplay(selectedDate)}</li>
                <li class="card-details-li">Time: ${slotSelectedLabel.textContent}</li>
                <li class="card-details-li">Phone: ${phoneNumber}</li>
                <li class="card-details-li">People: ${numberOfPeople}</li>
                <li class="card-details-li">Email: ${emailAddress}</li>
            </ul>
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
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
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
                selectedSlot = null;
                selectedDate = null;
                dateLabel.textContent = 'Select a date';
                dateInput.value = '';
                slotGrid.innerHTML = '<p class="slot-placeholder">Pick a date to see available slots</p>';
                slotSelected.style.display = 'none';

                // Refresh slots to show newly booked slot as unavailable
                if (selectedDate) fetchSlots();

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