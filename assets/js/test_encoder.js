function encoder(text) {
    // 将字符串转化为字符数组并转化成字节数组
    let bytes = [];
    for (let i = 0; i < text.length; i++) {
        bytes.push(text.charCodeAt(i));
    }

    // 将每个字节的后三位取反
    for (let i = 0; i < bytes.length; i++) {
        bytes[i] = bytes[i] ^ 0b00011111;
    }

    // 将字节数组转化为字符串
    return String.fromCharCode.apply(null, bytes);
}

function decoder(text) {
    // 将字符串转化为字符数组并转化成字节数组
    let bytes = [];
    for (let i = 0; i < text.length; i++) {
        bytes.push(text.charCodeAt(i));
    }

    // 将每个字节的后三位取反
    for (let i = 0; i < bytes.length; i++) {
        bytes[i] = bytes[i] ^ 0b00011111;
    }

    // 将字节数组转化为字符串
    return String.fromCharCode.apply(null, bytes);
}

// 用户输入待加密文本
const inputText = prompt("请输入要加密的文本：");

const encryptedText = encoder(inputText);
console.log("加密后的文本：", encryptedText);

const decryptedText = decoder(encryptedText);
console.log("解密后的文本：", decryptedText);
