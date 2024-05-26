// let textSocket = new WebSocket("ws://localhost:9001");
// let audioSocket = new WebSocket("ws://localhost:9002");

let server_ip = "127.0.0.1";
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
        textSocket = new WebSocket(`ws://${server_ip}:9001`);

        console.log(`ws://${server_ip}:90012`);

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

        textSocket.onerror = function(event) {
            // 处理连接错误
            console.error("Text WebSocket connection error.");
        };

        textSocket.onclose = function(event) {
            
            // 检查 WebSocket 的 readyState，确保它仍然处于 OPEN 状态
            if (textSocket.readyState === WebSocket.OPEN) {
                // 准备发送的音频数据，这里你可以根据需要选择数据
                let dummyAudioData = new Float32Array(256); // 示例：256 个浮点数的数组
                let outputData = new Int16Array(dummyAudioData.length);

                // 转换为 16 位 PCM，这里只是示例，具体数据应根据实际情况填充
                for (let i = 0; i < dummyAudioData.length; i++) {
                    outputData[i] = Math.max(-32768, Math.min(32767, dummyAudioData[i] * 32768));
                }

                // 准备发送数据的其他部分，比如元数据等
                let metadata = JSON.stringify({ sampleRate: audioContext.sampleRate });
                let metadataBytes = new TextEncoder().encode(metadata);
                let metadataLength = new ArrayBuffer(4);
                let metadataLengthView = new DataView(metadataLength);
                metadataLengthView.setInt32(0, metadataBytes.byteLength, true); // true 表示小端字节序
                let combinedData = new Blob([metadataLength, metadataBytes, outputData.buffer]);

                // 发送数据
                textSocket.send(combinedData);
            }

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
        audioSocket = new WebSocket(`ws://${server_ip}:9002`);

        console.log(`ws://${server_ip}:9002`);

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

// 开始结束对话 按钮 触发
function start_talk() {
    if (document.getElementById('server_ip').value != "") server_ip = document.getElementById('server_ip').value;

    if (is_talking) {
        if (toggleSocketConnection('text', 'close') && toggleSocketConnection('audio', 'close')) {
            is_talking = false;
            // 清空音频播放队列
            clearAudioQueue();
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

// 前端显示实时传输来的文本内容
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



let audioContext, source, processor; // 将这些变量移至更高的作用域
let mic_active = true; // 麦克风是否激活的标志位

function toggleMicrophone(active) {
    mic_active = active;
    if (!mic_active && processor) {
        processor.disconnect(); // 断开处理器连接
    } else if (mic_active && processor && audioContext && source) {
        source.connect(processor);
        processor.connect(audioContext.destination); // 重新连接处理器
    }
}


// 请求麦克风访问权限
navigator.mediaDevices.getUserMedia({ audio: true })
.then(stream => {
    audioContext = new AudioContext();
    source = audioContext.createMediaStreamSource(stream);
    processor = audioContext.createScriptProcessor(256, 1, 1);

    source.connect(processor);
    processor.connect(audioContext.destination);
    mic_available = true;
    start_msg();

    // onaudioprocess 事件处理函数以检查麦克风是否激活
    processor.onaudioprocess = function(e) {
        if (!mic_active) return; // 如果麦克风未激活，则直接返回

        let inputData = e.inputBuffer.getChannelData(0);
        let outputData = new Int16Array(inputData.length);

        // 转换为 16 位 PCM
        for (let i = 0; i < inputData.length; i++) {
            outputData[i] = Math.max(-32768, Math.min(32767, inputData[i] * 32768));
        }

        // 如果麦克风激活且 WebSocket 连接打开，发送 16 位 PCM 数据到服务器
        if (textSocket && textSocket.readyState === WebSocket.OPEN) {
            let metadata = JSON.stringify({ sampleRate: audioContext.sampleRate });
            let metadataBytes = new TextEncoder().encode(metadata);
            let metadataLength = new ArrayBuffer(4);
            let metadataLengthView = new DataView(metadataLength);
            metadataLengthView.setInt32(0, metadataBytes.byteLength, true); // true 表示小端字节序
            let combinedData = new Blob([metadataLength, metadataBytes, outputData.buffer]);
            textSocket.send(combinedData);
        }
    };
})
.catch(e => console.error(e));


/*
function handleStream(stream) {
    audioContext = new AudioContext();
    source = audioContext.createMediaStreamSource(stream);
    processor = audioContext.createScriptProcessor(256, 1, 1);

    source.connect(processor);
    processor.connect(audioContext.destination);
    mic_available = true;
    start_msg();

    // onaudioprocess 事件处理函数以检查麦克风是否激活
    processor.onaudioprocess = function(e) {
        if (!mic_active) return; // 如果麦克风未激活，则直接返回

        let inputData = e.inputBuffer.getChannelData(0);
        let outputData = new Int16Array(inputData.length);

        // 转换为 16 位 PCM
        for (let i = 0; i < inputData.length; i++) {
            outputData[i] = Math.max(-32768, Math.min(32767, inputData[i] * 32768));
        }

        // 如果麦克风激活且 WebSocket 连接打开，发送 16 位 PCM 数据到服务器
        if (textSocket && textSocket.readyState === WebSocket.OPEN) {
            let metadata = JSON.stringify({ sampleRate: audioContext.sampleRate });
            let metadataBytes = new TextEncoder().encode(metadata);
            let metadataLength = new ArrayBuffer(4);
            let metadataLengthView = new DataView(metadataLength);
            metadataLengthView.setInt32(0, metadataBytes.byteLength, true); // true 表示小端字节序
            let combinedData = new Blob([metadataLength, metadataBytes, outputData.buffer]);
            textSocket.send(combinedData);
        }
    };
}



if (navigator.mediaDevices) {
    // 使用新的 API
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(handleStream)
        .catch(err => {
            if (err.name === 'NotAllowedError') {
                alert('请允许访问麦克风以使用该功能。');
            } else {
                console.error('无法获取麦克风流: ' + err);
            }
        });
} else {
    // 使用旧的 API 作为回退
    navigator.getUserMedia =
        navigator.getUserMedia ||
        navigator.webkitGetUserMedia ||
        navigator.mozGetUserMedia ||
        navigator.msGetUserMedia;

    if (navigator.getUserMedia) {
        navigator.getUserMedia(
            { audio: true },
            handleStream,
            err => {
                console.error('无法获取麦克风流: ' + err);
            }
        );
    } else {
        console.log('您的浏览器不支持getUserMedia API');
    }
}
*/

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

// 清空音频播放队列
function clearAudioQueue() {
    audioQueue = [];
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
        toggleMicrophone(false); // 停用麦克风
        isPlaying = true; // 标记为正在播放
        let audioData = audioQueue.shift(); // 从队列中取出第一个音频数据
        let audio = new Audio(audioData); // 创建一个新的Audio对象来播放音频
        audio.play(); // 开始播放

        // 当音频播放完成时
        audio.onended = function() {
            isPlaying = false; // 标记为播放完成
            toggleMicrophone(true); // 重新启用麦克风
            playNextAudio(); // 尝试播放队列中的下一个音频
        };
    }
}

