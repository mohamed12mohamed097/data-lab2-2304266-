document.getElementById("add-form").addEventListener("submit", function (e) {
    const title = document.getElementById("title").value.trim();
    let message = "";

    if (title === "") message = "Title is required";
    else if (title.length > 200) message = "Title is too long (200 characters at most)";

    document.getElementById("error-title").textContent = message;
    if (message !== "") e.preventDefault();
});