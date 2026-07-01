
const form = document.getElementById("form");

form.addEventListener("submit", function(event) {
  event.preventDefault();

    const firstName = document.getElementById("firstName").value;
    const lastName = document.getElementById("lastName").value;
    const phoneNumber = document.getElementById("phoneNumber").value;
    const numberOfPeople = document.getElementById("numberOfPeople").value;
    const time = document.getElementById("time").value;
    const email = document.getElementById("email").value;
    const submit = document.getElementById("submit").value;

    console.log(firstName);
    console.log(lastName);
    console.log(phoneNumber);
    console.log(numberOfPeople);
    console.log(time);
    console.log(email);

    form.reset();
});