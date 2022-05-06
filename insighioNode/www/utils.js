function goBack() {
  window.history.back();
}

function setRadioGroupValue(groupName, valueToSelect){
  var elems = document.getElementsByName(groupName)

  for (var i = 0, length = elems.length; i < length; i++) {
    elems[i].checked = (elems[i].value === valueToSelect)
  }
}

function readRadioGroupValue(groupName, cookieName){
  var elems = document.getElementsByName(groupName)

  for (var i = 0, length = elems.length; i < length; i++) {
    if (elems[i].checked) {
      Cookies.set(cookieName, elems[i].value)
      break;
    }
  }
}

function enableElement(id, status) {
  var elem = document.getElementById(id)
  elem.disabled = !status
}

function elementIsVisible(elementId) {
  return document.getElementById(elementId).style.display === "block"
}

function checkboxStatusChanged(sensorId) {
  var checkBox = document.getElementById("input-" + sensorId + "-enable")
  showElement("address-" + sensorId, checkBox.checked)
}

function showElement(elementId, status) {
  var elem = document.getElementById(elementId)
  if(elem)
    elem.style.display = status ? "block" : "none"
}

function setElementValueIfNotUndefined(elementId, newValue, defaultValue=""){
  var elem = document.getElementById(elementId)
  if(elem)
    elem.value = newValue !== "undefined" && newValue !== undefined ? newValue : defaultValue
}
