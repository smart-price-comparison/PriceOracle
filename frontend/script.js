const searchBtn = document.getElementById("searchBtn");
const resultDiv = document.getElementById("result");

searchBtn.addEventListener("click", () => {
    const query = document.getElementById("searchInput").value.trim();
    if (!query) {
        resultDiv.innerText = "Please enter a product to search.";
        return;
    }

    resultDiv.innerText = "Scraping in progress...";
    searchBtn.disabled = true;

    fetch("http://127.0.0.1:5000/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query })
    })
    .then(async res => {
        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.error || `Search failed (${res.status})`);
        }
        return data;
    })
    .then(data => {
        console.log("Backend JSON:", data);

        resultDiv.innerHTML = ""; // ⭐ clear old results

        if (!data.results) {
            resultDiv.innerText = data.error || "Search failed. Please try again.";
            return;
        }

        const scraperErrors = Object.entries(data.errors || {})
            .map(([source, error]) => `${source}: ${error}`);
        if (scraperErrors.length) {
            const errorMessage = document.createElement("p");
            errorMessage.textContent = `Some searches failed: ${scraperErrors.join("; ")}`;
            resultDiv.appendChild(errorMessage);
        }

        // ⭐ helper to get cheapest product
        const getCheapest = (products) => {
            if (!products || products.length === 0) return null;
            return products.reduce((min, p) =>
                p.price && (!min || p.price < min.price) ? p : min
            , null);
        };

        const cheapestAmazon = getCheapest(data.results.amazon);
        const cheapestFlipkart = getCheapest(data.results.flipkart);
        const cheapestMyntra = getCheapest(data.results.myntra);

        // ⭐ helper to render product card
        const renderProduct = (title, product) => {
            if (!product) return "";

            const imageUrl = product.image_url || product.image || product.img;
            const imageMarkup = imageUrl
                ? `<img src="${imageUrl}" style="width:120px">`
                : "";

            return `
                <div style="margin-top:15px; border:1px solid #555; padding:10px;">
                    <h3>${title}</h3>
                    ${imageMarkup}
                    <strong>₹${product.price}</strong><br>
                    <a href="${product.url}" target="_blank">View Product</a>
                </div>
            `;
        };


        // ⭐ render to UI
        const productsHtml =
            renderProduct("Amazon (Cheapest)", cheapestAmazon) +
            renderProduct("Flipkart (Cheapest)", cheapestFlipkart) +
            renderProduct("Myntra (Cheapest)", cheapestMyntra);
        if (productsHtml) {
            resultDiv.insertAdjacentHTML("beforeend", productsHtml);
        } else if (!scraperErrors.length) {
            resultDiv.innerText = "No products found. Check the backend logs or try another search.";
        }

    })
    .catch(err => {
        console.error("Fetch error:", err);
        resultDiv.innerText = `Search failed: ${err.message}`;
    })
    .finally(() => {
        searchBtn.disabled = false;
    });
});
