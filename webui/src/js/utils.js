export function fetchInternal(url, timeout = 30000, method = "GET", body = null) {
  return new Promise((resolve, reject) => {
    const controller = new AbortController()
    const signal = controller.signal

    const timeoutId = setTimeout(() => {
      controller.abort()
      reject(new Error("Request timed out"))
    }, timeout)

    // Add cache-busting parameter
    const separator = url.includes("?") ? "&" : "?"
    const cacheBustUrl = url + separator + "_t=" + Date.now()

    const fetchOptions = {
      signal,
      method,
      cache: "no-cache",
      headers: {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        Pragma: "no-cache"
      }
    }

    // Add body for POST requests
    if (method === "POST" && body) {
      fetchOptions.headers["Content-Type"] = "application/json"
      fetchOptions.body = JSON.stringify(body)
    }

    fetch("http://192.168.4.1" + cacheBustUrl, fetchOptions)
      .then((response) => {
        clearTimeout(timeoutId)
        if (!response.ok) {
          return response.json().then((err) => {
            throw new Error(err.message || "Request failed")
          })
        }
        return response.json()
      })
      .then((data) => {
        resolve(data)
      })
      .catch((err) => {
        console.log("error fetching: ", url, ", e: ", err)
        reject(err)
      })
  })
}
