function showSidebar(){
    const sidebar = document.querySelector(`.sidebar`);
    sidebar.style.display = 'flex'
}

function hideSidebar() {
    const sidebar = document.querySelector(`.sidebar`);
    sidebar.style.display = 'none'
}

const form = document.getElementById("form");
const blurFilter = document.querySelector(".blur-filter");
const timeInput = document.getElementById("time");

const minDate = new Date();
minDate.setDate(minDate.getDate() + 1);
minDate.setHours(8, 30, 0, 0);

const maxDate = new Date(minDate);
maxDate.setDate(maxDate.getDate() + 30);
maxDate.setHours(23, 0, 0, 0);

function formatDateForInput(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
}

timeInput.min = formatDateForInput(minDate);
timeInput.max = formatDateForInput(maxDate);

// Keeps track of all confirmed reservation times
const bookedTimes = [];

form.addEventListener("submit", function(event) {
    event.preventDefault();

    const reservationCont = document.getElementById("reservations");
    const firstName = document.getElementById("firstName").value;
    const lastName = document.getElementById("lastName").value;
    const phoneNumber = document.getElementById("phoneNumber").value;
    const numberOfPeople = document.getElementById("numberOfPeople").value;
    const time = document.getElementById("time").value;
    const emailAddress = document.getElementById("email").value;
    const fullName = `${firstName} ${lastName}`;

    // Check if this time is already booked
    if (bookedTimes.includes(time)) {
        alert("This time slot is already booked. Please choose a different time.");
        return;
    }

    const dateObj = new Date(time);

    // Validate time is between 8:30 AM and 11:00 PM
    const selectedHour = dateObj.getHours();
    const selectedMinute = dateObj.getMinutes();
    const totalMinutes = selectedHour * 60 + selectedMinute;

    if (totalMinutes < 8 * 60 + 30 || totalMinutes > 23 * 60) {
        alert("Please choose a time between 8:30 AM and 11:00 PM.");
        return;
    }

    const formattedDate = dateObj.toLocaleString('en-GB', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
    });

    const newCard = document.createElement('div');
    newCard.className = 'reservation-card';
    newCard.innerHTML = `
        <h1 class="card-title">Reservation for ${fullName}</h1>
        <ul class="card-details">
            <li class="card-details-li">Time: ${formattedDate}</li>
            <li class="card-details-li">Phone Number: ${phoneNumber}</li>
            <li class="card-details-li">Number of people: ${numberOfPeople}</li>
            <li class="card-details-li">Email: ${emailAddress}</li>
        </ul>
    `;

    const cardModal = document.createElement('div');
    cardModal.className = 'card-modal';
    cardModal.innerHTML = `
        <h1 class="card-title">Reservation for ${fullName}</h1>
        <ul class="card-details">
            <li class="card-details-li">Time: ${formattedDate}</li>
            <li class="card-details-li">Phone Number: ${phoneNumber}</li>
            <li class="card-details-li">Number of people: ${numberOfPeople}</li>
            <li class="card-details-li">Email: ${emailAddress}</li>
        </ul>
        <button class="confirm-btn">Confirm</button>
        <button class="deny-btn">Deny</button>
    `;

    blurFilter.innerHTML = '';
    blurFilter.append(cardModal);
    blurFilter.style.visibility = "visible";
    document.getElementById("has-reservation").style.display = "none";

    const confirmBtn = cardModal.querySelector(".confirm-btn");
    const denyBtn = cardModal.querySelector(".deny-btn");

    confirmBtn.onclick = function() {
        blurFilter.style.visibility = "hidden";
        blurFilter.innerHTML = '';
        reservationCont.append(newCard);
        bookedTimes.push(time);
    }

    denyBtn.onclick = function() {
        blurFilter.style.visibility = "hidden";
        blurFilter.innerHTML = '';

        if (reservationCont.children.length === 0) {
            document.getElementById("has-reservation").style.display = "block";
        }
    }

    form.reset();
});