export function fetchInternal(url) {
  return new Promise((resolve, reject) => {
    fetch("http://192.168.4.1" + url)
      .then((response) => {
        return response.json()
      })
      .then((data) => {
        resolve(data)
      })
      .catch((err) => {
        console.log("error fetching: ", url, ", e: ", err)
        reject()
      })
  })
}
