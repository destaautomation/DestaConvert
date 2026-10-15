
const form = document.querySelector("form");
const button = form.querySelector('button[type="submit"]');

form.addEventListener("submit", function () {
    button.disabled = true;
    button.textContent = "Sedang mengonversi...";
});

