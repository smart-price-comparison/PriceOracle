import requests

url = "https://www.amazon.in/s?k=nike+shoes"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebSite/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-IN,en;q=0.9"
}

r = requests.get(url, headers=headers)
print("Status:", r.status_code)
print("First 300 chars:\n", r.text[:300])
