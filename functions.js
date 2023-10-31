var client = new Paho.MQTT.Client("broker.hivemq.com", 8000, "client_" + new Date().getTime());
 
    client.connect({onSuccess:onConnect});            
 
 
    function onConnect() {
    console.log('Connected to MQTT broker');
}
 
    function scheduleTap(tapNumber) {
        var dateInput = document.getElementById('tap' + tapNumber + 'Date');
        var timeInput = document.getElementById('tap' + tapNumber + 'Time');
 
        var dateValue = dateInput.value;
        var timeValue = timeInput.value;
 
        var message = {
            tapNumber: tapNumber,
            date: dateValue,
            time: timeValue
        };
 
        var messageString = JSON.stringify(message);
 
        var topic = 'schedule_tap';
 
        var message = new Paho.MQTT.Message(messageString);
        message.destinationName = topic;
        client.send(message);
}
 
 
 
document.addEventListener('DOMContentLoaded', function () {
        const presetSelect = document.getElementById('presetSelect');
        const addPresetButton = document.getElementById('addPreset'); 	
        const editPresetButton = document.getElementById('editPreset');
        const removePresetButton = document.getElementById('removePreset');
        const submitScheduleButton = document.getElementById('submitSchedule');
 
 
    function updatePresetSelect() {
        presetSelect.innerHTML = '<option value="" disabled selected>Select a Preset</option>';
        presets.forEach((preset, index) => {
            const option = document.createElement('option');
            option.value = index;
            option.textContent = preset.name;
            presetSelect.appendChild(option);
        });
    }
 
    function savePresets() {
        document.cookie = `presets=${JSON.stringify(presets)}; expires=Fri, 31 Dec 9999 23:59:59 GMT`;
    }
 
    function loadPresets() {
        const cookieValue = document.cookie.replace(/(?:(?:^|.*;\s*)presets\s*=\s*([^;]*).*$)|^.*$/, "$1");
        if (cookieValue) {
            presets = JSON.parse(cookieValue);
            updatePresetSelect();
        }
    }
    function removeSelectedPreset() {
        const selectedIndex = presetSelect.value;
        if (selectedIndex !== '') {
            const confirmDelete = confirm("Are you sure you want to delete this preset?");
            if (confirmDelete) {
                presets.splice(selectedIndex, 1);
                savePresets();
                updatePresetSelect();
            }
        }
    }
 
    let presets = [];
 
    loadPresets();
 
 
function getSelectedDays() {
    const checkboxes = document.querySelectorAll('input[type="checkbox"][name="day"]');
    const selectedDays = [];
    checkboxes.forEach(function(checkbox) {
        if (checkbox.checked) {
            selectedDays.push(checkbox.value);
        }
    });
    return selectedDays;
}
 
 
 
    addPresetButton.addEventListener('click', function() {
        const presetName = prompt('Enter the name for the new preset:');
    if (presetName) {
        const presetDays = prompt('Enter the days for the preset (comma-separated, e.g., Mon,Tue,Wed):');
        const presetTime = prompt('Enter the time for the preset (HH:MM):');
        const newPreset = {
            name: presetName,
            days: presetDays.split(','),
            time: presetTime
        };
        presets.push(newPreset);
        savePresets();
        updatePresetSelect();
    }
    });
 
    editPresetButton.addEventListener('click', function() {
        const selectedIndex = presetSelect.value;
        if (selectedIndex !== '') {
            const selectedPreset = presets[selectedIndex];
            const presetName = prompt('Enter the new name for the preset:', selectedPreset.name);
            if (presetName) {
                const presetDays = prompt('Enter the new days for the preset (comma-separated, e.g., Mon,Tue,Wed):', selectedPreset.days.join(','));
 
                const presetTime = prompt('Enter the new time for the preset (HH:MM):', selectedPreset.time);
                selectedPreset.name = presetName;
                selectedPreset.days = presetDays.split(',');
                selectedPreset.time = presetTime;
                savePresets();
                updatePresetSelect();
            }
        }
    });
 
    submitScheduleButton.addEventListener('click', function() {
        for (var i = 1; i <= 3; i++) {
            setTimeout(function (tap) {
                return function () {
                    scheduleTap(tap);
                }
            }(i));
        }
        alert('Schedules submitted!');
 
    });
 
    presetSelect.addEventListener('change', function() {
        const selectedIndex = presetSelect.value;
    if (selectedIndex !== '') {
        const selectedPreset = presets[selectedIndex];
 
        const message = {
            days: selectedPreset.days.join(','),
            time: selectedPreset.time
        };
 
        const messageString = JSON.stringify(message);
 
        const topic = 'schedule/preset';
 
        const mqttMessage = new Paho.MQTT.Message(messageString);
        mqttMessage.destinationName = topic;
        client.send(mqttMessage);
 
        // Display selected preset information
        var selectedPresetInfo = document.getElementById('selectedPresetInfo');
        selectedPresetInfo.textContent = `Relays will be activated on ${selectedPreset.days.join(', ')} at ${selectedPreset.time}`;
 
        // Disable schedule buttons and make date/time inputs read-only
        var tapDates = document.getElementsByClassName('tapDate');
        var tapTimes = document.getElementsByClassName('tapTime');
        var scheduleButtons = document.getElementsByClassName('scheduleButton');
 
        for (let i = 0; i < tapDates.length; i++) {
            tapDates[i].readOnly = true;
            tapTimes[i].readOnly = true;
            scheduleButtons[i].disabled = true;
        }
    } else {
        // Enable schedule buttons and enable date/time inputs if no preset is selected
        var tapDates = document.getElementsByClassName('tapDate');
        var tapTimes = document.getElementsByClassName('tapTime');
        var scheduleButtons = document.getElementsByClassName('scheduleButton');
 
        for (let i = 0; i < tapDates.length; i++) {
            tapDates[i].readOnly = false;
            tapTimes[i].readOnly = false;
            scheduleButtons[i].disabled = false;
        }
 
        // Clear selected preset info
        var selectedPresetInfo = document.getElementById('selectedPresetInfo');
        selectedPresetInfo.textContent = '';
    }
    });
    removePresetButton.addEventListener('click', removeSelectedPreset);
});
