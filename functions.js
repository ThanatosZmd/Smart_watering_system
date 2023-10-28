client = new Paho.MQTT.Client("164.138.216.127", Number(9001))
client.subscribe("settaps")
function tst1(){
	state = 0
	if (state == 0){
		state = 1 
		var msg = new Paho.MQTT.Message("1")
		msg.destinationName = "topic" //here goes the topic(I belive it is settaps)
		client.send(msg)
		this.innerHTML = "Taps on";
	} else if (state == 1){
		state = 0 
		var msg = new Paho.MQTT.Message("0")
		msg.destinationName = "topic" //here goes the topic(I belive it is settaps)
		
		this.innerHTML = "Taps off";
	client.send(msg)
	}
}
// Get references to the HTML elements
const valueElement = document.getElementById('value');
const updateButton = document.getElementById('updateButton');

let counter = 0; // Initial value

// Function to update the value
function updateValue() {
  counter++;
  valueElement.textContent = counter;
}

// Add an event listener to the button
updateButton.addEventListener('click', updateValue);


//topics are: settaps; chacktaps; 