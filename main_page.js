var client = new Paho.MQTT.Client("broker.hivemq.com", 8000, "client_" + new Date().getTime());
 
client.onConnectionLost = function (responseObject) {
        console.log("Connection lost: " + responseObject.errorMessage);
    };
 
function toggleTap(tapNumber) {
    var message = new Paho.MQTT.Message(tapNumber.toString());
    message.destinationName = "settaps";
    client.send(message);
}
 
    client.connect({
        onSuccess: function () {
            console.log("Connected to MQTT broker");
            client.subscribe("sgarden/weather");
        },
        onFailure: function (responseObject) {
            console.log("Failed to connect: " + responseObject.errorMessage);
        }
        });
        client.onMessageArrived = function (message) {
    if (message.destinationName === "sgarden/weather") {
        var payloadString = message.payloadString;
        var data = parseTempHumidityString(payloadString);
 
        document.getElementById("temperatureValue").innerText = data.temperature + "°C";
        document.getElementById("humidityValue").innerText = data.humidity + "%";
    }
}
 
function parseTempHumidityString(payloadString) {
    var parts = payloadString.split(' ');
    var tempValue = parts[0].split(':')[1];
    var humidityValue = parts[3];
 
    return {
        temperature: parseFloat(tempValue),
        humidity: parseInt(humidityValue)
    };
}