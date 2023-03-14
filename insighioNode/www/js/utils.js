function goBack() {
  window.history.back()
}

function setRadioGroupValue(groupName, valueToSelect) {
  var elems = document.getElementsByName(groupName)

  for (var i = 0, length = elems.length; i < length; i++) {
    elems[i].checked = elems[i].value === valueToSelect
  }
}

function readRadioGroupValue(groupName, cookieName) {
  var elems = document.getElementsByName(groupName)

  for (var i = 0, length = elems.length; i < length; i++) {
    if (elems[i].checked) {
      Cookies.set(cookieName, elems[i].value)
      break
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
  if (elem) elem.style.display = status ? "block" : "none"
}

function setElemValue(elementId, newValue, defaultValue = "", intZeroAccepted = true) {
  var elem = document.getElementById(elementId)
  if (!elem) {
    console.log("setElemValue: Element not found: ", elementId)
    return
  }

  elem.value =
    newValue !== "" && newValue !== "undefined" && newValue !== undefined && (intZeroAccepted || (!intZeroAccepted && newValue !== 0))
      ? newValue
      : defaultValue
}

function setElemValueBool(elementId, newValue, defaultValue = "", boolField = "checked") {
  var elem = document.getElementById(elementId)
  if (!elem) {
    console.log("setElemValueBool: Element not found: ", elementId)
    return
  }

  elem[boolField] = newValue !== "" && newValue !== "undefined" && newValue !== undefined ? Boolean(newValue) : defaultValue
}

function validateElemValue(elemId, message, regex = undefined) {
  var fieldObj = document.getElementById(elemId)
  if (!fieldObj) {
    console.log("validateElemValue: Element not found: ", elemId)
    return false
  }

  var value = fieldObj.value.trim()
  if (value == "" || (regex && !new RegExp(regex, "g").exec(value))) {
    fieldObj.style.borderColor = "red"
    fieldObj.focus()
    window.alert("Please enter a valid " + message)
    return false
  }
  fieldObj.style.borderColor = "green"
  return true
}

function boolElemToPyStr(elemId, boolField = "checked") {
  var fieldObj = document.getElementById(elemId)
  if (!fieldObj) {
    console.log("boolElemToPyStr: Element not found: ", elemId)
    return undefined
  }

  return fieldObj[boolField] ? "True" : "False"
}

function isChecked(elemId) {
  var fieldObj = document.getElementById(elemId)
  return fieldObj && fieldObj["checked"]
}

function addElemChild(parentElem, txt, val) {
  var elem = document.createElement("option")
  if (val) elem.value = val
  elem.innerHTML = txt
  parentElem.appendChild(elem)
}

function addSwitch(parentId, switchId, switchLabel, onClickCallback = undefined) {
  var parent = document.getElementById(parentId)

  // var mainDiv = document.createElement("div")
  // mainDiv.classList.add('form-group')

  ///////////////////////////////////////////////////////
  var labelDiv = document.createElement("div")
  labelDiv.classList.add("col-4")
  labelDiv.classList.add("col-lg-6")
  labelDiv.classList.add("col-sm-10")

  var label = document.createElement("label")
  label.classList.add("form-label")
  label.appendChild(document.createTextNode(switchLabel))

  labelDiv.appendChild(label)
  parent.appendChild(labelDiv)

  ///////////////////////////////////////////

  var switchDiv = document.createElement("div")
  switchDiv.classList.add("col-8")
  switchDiv.classList.add("col-lg-6")
  switchDiv.classList.add("col-sm-2")

  // var switchDivGroup = document.createElement("div") // not sure if needed
  // switchDivGroup.classList.add('form-group')

  var switchLabel = document.createElement("label")
  switchLabel.classList.add("form-switch")

  var switchInput = document.createElement("input")
  switchInput.type = "checkbox"
  switchInput.id = switchId
  if (onClickCallback) switchInput.onclick = onClickCallback

  var switchIcon = document.createElement("i")
  switchIcon.classList.add("form-icon")

  switchLabel.appendChild(switchInput)
  switchLabel.appendChild(switchIcon)
  switchDiv.appendChild(switchLabel)
  parent.appendChild(switchDiv)
}

function strToJSValue(strVal) {
  if (strVal === "undefined" || strVal === "") return undefined
  else if (strVal === "true") return true
  else if (strVal === "false") return false
  return strVal
}

function generateOptions(parentId, optionsData) {
  var parent = document.getElementById(parentId)

  for (const [key, value] of Object.entries(optionsData)) {
    var label = document.createElement("option")
    label.value = key
    label.appendChild(document.createTextNode(value))
    parent.appendChild(label)
  }
}

function enableNavigationButtons() {
  document.getElementById("save-button").disabled = false
  document.getElementById("back-button").disabled = false
}

function disableNavigationButtons() {
  document.getElementById("save-button").disabled = true
  document.getElementById("back-button").disabled = true
}

function detectBoardChange(settings_mac, cookies_mac){
  console.log("Board mac: ", settings_mac, ", Cookie mac: ", cookies_mac)
  if (settings_mac !== undefined && settings_mac !== cookies_mac) {
    alert("board change detected...restarting configuration")
    location.href = "step-2-select.html"
    return
  }
}

function fromMultiWordToOne(initialString, delimeter=" ") {
  try {
    if(!initialString || typeof(initialString) !== "string")
      return initialString

    return initialString.split(delimeter)[0]
  }
  catch {
    return initialString
  }
}
