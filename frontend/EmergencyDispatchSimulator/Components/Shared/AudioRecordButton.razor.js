let _stream;
let _audioChunks;
let _mediaRecorder;
let _dotnet;

export function initialize(dotnet) {
    _dotnet = dotnet;
}

export async function startRecording () {
    _stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    _mediaRecorder = new MediaRecorder(_stream);
    _mediaRecorder.addEventListener('dataavailable', vEvent => {
        _audioChunks.push(vEvent.data);
    });

    _mediaRecorder.addEventListener('error', error => {
        console.warn('media recorder error: ' + error);
    });

    _mediaRecorder.addEventListener('stop', async () => {
        var pAudioBlob = new Blob(_audioChunks, { type: "audio/wav" });
        let pAudioUrl = URL.createObjectURL(pAudioBlob);
        const b64Str = await blobToBase64(pAudioBlob);
        _dotnet.invokeMethodAsync('OnRecordingCompleted', b64Str);

        // uncomment if you want to play the recorded audio (without the using the audio HTML element)
        // let pAudio = new Audio(pAudioUrl);
        // await pAudio.play();
    });

    _audioChunks = [];
    _mediaRecorder.start();
}

export async function stopRecording () {
    _mediaRecorder.stop();
    _stream.getTracks().forEach(pTrack => pTrack.stop());
}

export async function downloadRecording (url, name) {
    // Create a link element
    const link = document.createElement("a");

    // Set the link's href to point to the Blob URL
    link.href = url;
    link.download = name;

    // Append link to the body
    document.body.appendChild(link);

    // Dispatch click event on the link
    // This is necessary as link.click() does not work on the latest firefox
    link.dispatchEvent(
        new MouseEvent('click', {
            bubbles: true,
            cancelable: true,
            view: window
        })
    );

    // Remove the link from the body
    document.body.removeChild(link);
}



function blobToBase64(blob) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => {
            // reader.result is a data URL (e.g., "data:audio/wav;base64,...")
            // We split to get only the base64 part
            const base64data = reader.result.split(',')[1];
            resolve(base64data);
        };
        reader.onerror = reject;
        reader.readAsDataURL(blob);
    });
}