export function fetchInternal(url, timeout = 30000, method = "GET", body = null, responseType = "json") {
  return new Promise((resolve, reject) => {
    const controller = new AbortController()
    const signal = controller.signal

    const timeoutId = setTimeout(() => {
      controller.abort()
      reject(new Error("Request timed out"))
    }, timeout)

    // Add cache-busting parameter
    // const separator = url.includes("?") ? "&" : "?"
    // const cacheBustUrl = url + separator + "_t=" + Date.now()

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

    fetch("http://192.168.4.1" + url, fetchOptions)
      .then((response) => {
        clearTimeout(timeoutId)

        // If responseType is 'response', return the raw response object
        if (responseType === "response") {
          console.log("response raw")
          return response
        }

        if (!response.ok) {
          // Try to parse error as JSON, but don't fail if it's not JSON
          return response.text().then((text) => {
            try {
              console.log("response not ok, trying to parse error JSON")
              const err = JSON.parse(text)
              throw new Error(err.message || `Request failed with status: ${response.status}`)
            } catch (e) {
              console.log("Error parsing JSON response: ", e)
              throw new Error(`Request failed with status: ${response.status}`)
            }
          })
        }
        console.log("response ok, processing response")

        // Handle response based on responseType
        if (responseType === "text") {
          console.log("response text")
          try {
            return response.text()
          } catch (e) {
            console.log("Error parsing text response: ", e)
          }
        }
        // else if (responseType === "json") {
        //   console.log("response json")
        //   // Try JSON first, fallback to text
        //   try {
        //     return response.json()
        //   } catch (e) {
        //     console.log("Error parsing JSON response: ", e)
        //   }
        // }

        console.log("response fallback")
        // Default: auto-detect
        return response.text().then((text) => {
          try {
            console.log("response fallback JSON: ", text)
            return JSON.parse(text)
          } catch (e) {
            console.log("Error parsing JSON response: ", e)
            return text
          }
        })
      })
      .then((data) => {
        console.log("fetched: ", url, ", data: ", data)
        resolve(data)
      })
      .catch((err) => {
        clearTimeout(timeoutId)
        console.log("error fetching: ", url, ", e: ", err)
        reject(err)
      })
  })
}
