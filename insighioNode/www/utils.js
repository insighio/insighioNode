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

function setElemValue(elementId, newValue, defaultValue="", intZeroAccepted=true){
  var elem = document.getElementById(elementId)
  if(!elem) {
    console.log("setElemValue: Element not found: ", elementId)
    return
  }

  elem.value = (newValue !== "undefined" && newValue !== undefined && (intZeroAccepted || (!intZeroAccepted && newValue !== 0))) ? newValue : defaultValue
}

function setElemValueBool(elementId, newValue, defaultValue="", boolField="checked"){
  var elem = document.getElementById(elementId)
  if(!elem) {
    console.log("setElemValueBool: Element not found: ", elementId)
    return
  }

  elem[boolField] = (newValue !== "undefined" && newValue !== undefined) ? Boolean(newValue) : defaultValue
}

function validateElemValue(elemId, message, regex=undefined) {
  var fieldObj = document.getElementById(elemId)
  if(!fieldObj) {
    console.log("validateElemValue: Element not found: ", elemId)
    return false
  }

  var value = fieldObj.value.trim()
  if(value == "" || (regex && !((new RegExp(regex, 'g')).exec(value)))) {
      fieldObj.style.borderColor = "red";
      fieldObj.focus()
      window.alert("Please enter a valid " + message)
      return false
  }
  fieldObj.style.borderColor = "green";
  return true
}

function boolElemToPyStr(elemId, boolField="checked") {
  var fieldObj = document.getElementById(elemId)
  if(!fieldObj) {
    console.log("boolElemToPyStr: Element not found: ", elemId)
    return false
  }

  return fieldObj[boolField] ? "True" : "False"
}

function addElemChild(parentElem, txt, val){
    var elem = document.createElement("option")
    if(val)
        elem.value = val
    elem.innerHTML = txt
    parentElem.appendChild(elem)
}
