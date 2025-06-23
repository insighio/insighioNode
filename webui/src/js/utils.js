export function fetchInternal(url, method = "GET", timeout = 30000, headers = {}, body = null) {
  return new Promise((resolve, reject) => {
    const controller = new AbortController()
    const signal = controller.signal

    const timeoutId = setTimeout(() => {
      controller.abort()
      reject(new Error("Request timed out"))
    }, timeout)

    fetch("http://192.168.4.1" + url, { signal, method, headers, body })
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
