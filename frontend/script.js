const searchBtn = document.getElementById("searchBtn");
const resultDiv = document.getElementById("result"); // make sure you have a <div id="result"></div> in your HTML

searchBtn.addEventListener("click", () => {
    const query = document.getElementById("searchInput").value.trim();
    if (!query) {
        resultDiv.innerText = "Please enter a product to search.";
        return;
    }

    // Show loading message
    resultDiv.innerText = "Scraping in progress... Please wait.";
    searchBtn.disabled = true;

    fetch("http://127.0.0.1:5000/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query })
    })
    .then(res => res.json())
    .then(data => {
        // Show success message
        resultDiv.innerText = data.message || "Scraper ran successfully!";
    })
    .catch(err => {
        console.error(err);
        resultDiv.innerText = "An error occurred while running the scraper.";
    })
    .finally(() => {
        searchBtn.disabled = false;
    });
});

