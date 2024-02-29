// let textSocket = new WebSocket("ws://localhost:9001");
// let audioSocket = new WebSocket("ws://localhost:9002");
let textSocket = null;
let audioSocket = null;
let displayDiv = document.getElementById('textDisplay');
let server_available = false;
let mic_available = false;
let fullSentences = [];
// 聊天中的标志位
let is_talking = false;

const serverCheckInterval = 5000; // Check every 5 seconds

function connectToTextServer() {
    try {
        textSocket = new WebSocket("ws://localhost:9001");

        textSocket.onopen = function(event) {
            server_available = true;
            start_msg();
        };

        textSocket.onmessage = function(event) {
            let data = JSON.parse(event.data);
        
            if (data.type === 'realtime') {
                displayRealtimeText(data.text, displayDiv);
            } else if (data.type === 'fullSentence') {
                fullSentences.push(data.text);
                displayRealtimeText("", displayDiv); // Refresh display with new full sentence
            }
        };

        audioSocket.onerror = function(event) {
            // 处理连接错误
            console.error("Text WebSocket connection error.");
        };

        textSocket.onclose = function(event) {
            server_available = false;
        };

        return true;
    } catch (error) {
        console.error('Error connecting to text server:', error);

        return false;
    }
}

// 连接到音频服务器
function connectToAudioServer() {
    try {
        audioSocket = new WebSocket("ws://localhost:9002");

        audioSocket.onopen = function(event) {
            // 处理连接打开
        };

        // 修改audioSocket.onmessage处理函数，以处理接收到的音频数据
        audioSocket.onmessage = function(event) {
            let data = JSON.parse(event.data);

            if (data.type === 'audio') {
                onAudioReceived(data.audioData, data.format); // 使用音频数据和格式
            }

            // if (data.type === 'realtime') {
            //     displayRealtimeText(data.text, displayDiv);
            // } else if (data.type === 'fullSentence') {
            //     fullSentences.push(data.text);
            //     displayRealtimeText("", displayDiv); // 刷新显示以显示新的完整句子
            // } else if (data.type === 'audio') {
            //     onAudioReceived(data.audioUrl); // 处理接收到的音频数据
            // }
        };

        audioSocket.onclose = function(event) {
            // 处理连接关闭
        };

        audioSocket.onerror = function(event) {
            // 处理连接错误
            console.error("Audio WebSocket connection error.");
        };

        return true;
    } catch (error) {
        console.error('Error connecting to audio server:', error);
        return false;
    }
}

// 通用函数来控制socket的开关
function toggleSocketConnection(socketType, action) {
    try {
        if (socketType === 'text') {
            if (textSocket != null) {
                if (action === 'open' && textSocket.readyState !== WebSocket.OPEN) {
                    return connectToTextServer(); // 调用已有的连接函数
                } else if (action === 'close' && textSocket.readyState === WebSocket.OPEN) {
                    textSocket.close(); // 关闭socket连接
                }
            } else {
                if (action === 'open') {
                    return connectToTextServer(); // 连接到音频服务器
                } else if (action === 'close') {
                    // textSocket.close(); // 关闭socket连接
                }
            }
            
        } else if (socketType === 'audio') {
            if (audioSocket != null) {
                if (action === 'open' && (!audioSocket || audioSocket.readyState !== WebSocket.OPEN)) {
                    return connectToAudioServer(); // 连接到音频服务器
                } else if (action === 'close' && audioSocket && audioSocket.readyState === WebSocket.OPEN) {
                    audioSocket.close(); // 关闭socket连接
                }
            } else {
                if (action === 'open') {
                    return connectToAudioServer(); // 连接到音频服务器
                } else if (action === 'close') {
                    // audioSocket.close(); // 关闭socket连接
                }
            }
        }   

        return true;
    } catch (error) {
        console.error('Error toggling socket connection:', error);
        return false;
    }
    
}

function start_talk() {
    if (is_talking) {
        if (toggleSocketConnection('text', 'close') && toggleSocketConnection('audio', 'close')) {
            is_talking = false;
            document.getElementById("start_talk_btn").innerHTML = "开始对话";
        } else {
            console.error("Error closing socket connections");
        }
    } else {
        if (toggleSocketConnection('text', 'open') && toggleSocketConnection('audio', 'open')) {
            is_talking = true;
            document.getElementById("start_talk_btn").innerHTML = "结束对话";
        } else {
            console.error("Error Opening socket connections");
            alert("建立websocket连接失败，请确认服务端是否已经启动 或 网络等问题");
        }
    }
}


function displayRealtimeText(realtimeText, displayDiv) {
    let displayedText = fullSentences.map((sentence, index) => {
        let span = document.createElement('span');
        span.textContent = sentence + " ";
        span.className = index % 2 === 0 ? 'yellow' : 'cyan';
        return span.outerHTML;
    }).join('') + realtimeText;

    displayDiv.innerHTML = displayedText;
}

function start_msg() {
    if (!mic_available)
        displayRealtimeText("🎤  请允许麦克风输入  🎤", displayDiv);
    else if (!server_available)
        displayRealtimeText("🖥️  请运行服务端  🖥️", displayDiv);
    else
        displayRealtimeText("👄  请开始说话  👄", displayDiv);
};

// Check server availability periodically 自动连接socket
// setInterval(() => {
//     if (!server_available) {
//         connectToTextServer();
//     }
// }, serverCheckInterval);

start_msg()



// Request access to the microphone
navigator.mediaDevices.getUserMedia({ audio: true })
.then(stream => {
    let audioContext = new AudioContext();
    let source = audioContext.createMediaStreamSource(stream);
    let processor = audioContext.createScriptProcessor(256, 1, 1);

    source.connect(processor);
    processor.connect(audioContext.destination);
    mic_available = true;
    start_msg()

    processor.onaudioprocess = function(e) {
        let inputData = e.inputBuffer.getChannelData(0);
        let outputData = new Int16Array(inputData.length);

        // Convert to 16-bit PCM
        for (let i = 0; i < inputData.length; i++) {
            outputData[i] = Math.max(-32768, Math.min(32767, inputData[i] * 32768));
        }

        // Send the 16-bit PCM data to the server

        if (textSocket) {

        
            if (textSocket.readyState === WebSocket.OPEN) {
                // Create a JSON string with metadata
                let metadata = JSON.stringify({ sampleRate: audioContext.sampleRate });
                // Convert metadata to a byte array
                let metadataBytes = new TextEncoder().encode(metadata);
                // Create a buffer for metadata length (4 bytes for 32-bit integer)
                let metadataLength = new ArrayBuffer(4);
                let metadataLengthView = new DataView(metadataLength);
                // Set the length of the metadata in the first 4 bytes
                metadataLengthView.setInt32(0, metadataBytes.byteLength, true); // true for little-endian
                // Combine metadata length, metadata, and audio data into a single message
                let combinedData = new Blob([metadataLength, metadataBytes, outputData.buffer]);
                textSocket.send(combinedData);
            }
        }
    };
})
.catch(e => console.error(e));



let audioQueue = []; // 音频播放队列
let isPlaying = false; // 标记当前是否有音频正在播放

function base64ToBlob(base64, mimeType) {
    const byteCharacters = atob(base64);
    const byteArrays = [];

    for (let offset = 0; offset < byteCharacters.length; offset += 1024) {
        const slice = byteCharacters.slice(offset, offset + 1024);
        const byteNumbers = new Array(slice.length);

        for (let i = 0; i < slice.length; i++) {
            byteNumbers[i] = slice.charCodeAt(i);
        }

        const byteArray = new Uint8Array(byteNumbers);
        byteArrays.push(byteArray);
    }

    const blob = new Blob(byteArrays, {type: mimeType});
    return blob;
}


// 当接收到音频数据时的处理函数
function onAudioReceived(audioData, audioFormat) {
    // 将Base64编码的字符串解码为二进制数据
    let audioBlob = base64ToBlob(audioData, `audio/${audioFormat}`); // 使用动态音频格式
    let audioUrl = URL.createObjectURL(audioBlob); // 创建Blob URL

    audioQueue.push(audioUrl); // 将Blob URL添加到播放队列
    playNextAudio(); // 尝试播放下一个音频
}

// 播放队列中的下一个音频
function playNextAudio() {
    if (!isPlaying && audioQueue.length > 0) {
        isPlaying = true; // 标记为正在播放
        let audioData = audioQueue.shift(); // 从队列中取出第一个音频数据
        let audio = new Audio(audioData); // 创建一个新的Audio对象来播放音频
        audio.play(); // 开始播放

        // 当音频播放完成时
        audio.onended = function() {
            isPlaying = false; // 标记为播放完成
            playNextAudio(); // 尝试播放队列中的下一个音频
        };
    }
}

