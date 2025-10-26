let _audio;
let _dotnet;

export function initialize(dotnet) {
    _dotnet = dotnet;
}

export function playB64Wav(b64Wav) {
    // pause/stop audio
    if (_audio) {
        _audio.src = "";
    }

    _audio = new Audio("data:audio/wav;base64," + b64Wav);

    _audio.addEventListener("ended", function() {
        if (_dotnet) {
            _dotnet.invokeMethodAsync("OnAudioStopped");
            _audio.src = "";
        }
    });

    _audio.play();
}