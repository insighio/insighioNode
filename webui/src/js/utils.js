export function fetchInternal(url, timeout = 30000, method = "GET") {
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

    fetch("http://192.168.4.1" + cacheBustUrl, {
      signal,
      method,
      cache: "no-cache",
      headers: {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        Pragma: "no-cache"
      }
    })
      .then((response) => {
        clearTimeout(timeoutId)
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
