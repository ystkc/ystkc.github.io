function encoder(array, no_convert = false) {
    // 将每个字节后5bit取反
    if (no_convert) {
        var result = [];
        for (let i = 0; i < array.length; i++) {
            result.push(array[i] ^ 0x1F);
        }
        return result;
    } else {
        const byteArray = new Uint8Array(array);
        const processedArray = new Uint8Array(byteArray.length);
        for (let i = 0; i < byteArray.length; i++) {
            // 获取后5位并取反
            processedArray[i] = (byteArray[i] ^ 0x1F);
        }
        // 将处理后的字节转换为字符串
        return new TextDecoder('utf-8').decode(processedArray);
    }
}


async function fetchBin(url, index, total) {  
    return await fetch(url.replace(".zip", ""))  
    .then(response => {
        if (!response.ok) {
            // throw new Error(`网络错误: ${response.status} ${response.statusText}`);
        }
        return response.arrayBuffer();
    })  
    .then(data => {  
        document.querySelector("#results").innerHTML += `第 ${index}/${total} 个词库加载完成！<br>`;
        return JSON.parse(encoder(data));  
    })  
    .catch(error => {  
        console.error(error);  
        document.querySelector("#results").innerHTML += `加载备份JSON时发生错误: ${error.message}<br>`;
    });  
}
async function fetchBinAndUnzip(url, index, total) {  
    // document.querySelector("#results").innerHTML += `正在加载第 ${index} / ${total} 个词库，请稍候...<br>`;
    
    return await fetch(url)  
        .then(response => {
            if (!response.ok) {
                // 处理404错误或其他HTTP错误，抛出一个错误
                throw new Error(`网络错误: ${response.status} ${response.statusText}`);
            }
            return response.arrayBuffer();
        })  
        .then(data => {  
            const zip = new JSZip();  
            return zip.loadAsync(data) // 直接使用 ArrayBuffer
                .then(zip => {  
                    const files = Object.keys(zip.files);  
                    const file = files[0];  
                    return zip.file(file).async('arraybuffer');  
                })  
                .then(data => {  
                    document.querySelector("#results").innerHTML += `第 ${index}/${total} 个词库加载完成！<br>`;
                    return JSON.parse(encoder(data));  
                });  
        })  
        .catch(error => {  
            // console.error(error);
            // document.querySelector("#results").innerHTML += `加载第 ${index} 个词库时发生错误: ${error.message}<br>`;
            // 可能没有zip，直接请求binary文件
            return fetchBin(url, index, total)
        });  
}


let url;

const acceptWordsUrl = "assets/accept_words.bin.zip";  
const badWordsUrl = "assets/bad_words.bin.zip";  
const enhancedBadWordsUrl = "assets/enhanced_bad_words.bin.zip";
const warnWordsUrl = "assets/warn_words.bin.zip"; 

let badWords, enhancedBadWords, acceptWords, warnWords;  
let acceptWordsSet, warnWordsSet, badWordsSet, enhancedBadWordsSet;  
async function init() {  
    // 设置输入框为disabled
    document.querySelector("#notice-input").disabled = true;
    document.querySelector("#notice-input").value = "正在加载词库...请稍候...";
    url = window.location.href; // http://127.0.0.1:4000/
    [badWords, acceptWords, enhancedBadWords, warnWords] = await Promise.all([  
        fetchBinAndUnzip(url + badWordsUrl, 1, 4),  
        fetchBinAndUnzip(url + acceptWordsUrl, 2, 4),  
        fetchBinAndUnzip(url + enhancedBadWordsUrl, 3, 4),
        fetchBinAndUnzip(url + warnWordsUrl, 4, 4)  
    ]);  
    if (badWords === undefined || acceptWords === undefined || enhancedBadWords === undefined || warnWords === undefined) {
        document.querySelector("#notice-input").value = "词库加载失败！请刷新网页 或 更换浏览器。";
        document.querySelector("#results").innerHTML += "词库加载失败！请刷新网页 或 更换浏览器。<br>";
        return;
    }
    document.querySelector("#notice-input").disabled = false;
    document.querySelector("#notice-input").value = "";
    document.querySelector("#results").innerHTML += "初始化完成！<br>";
    document.querySelector("#results").innerHTML += acceptWords[0];
    acceptWords.shift();

    acceptWordsSet = new Set(acceptWords);  
    warnWordsSet = new Set(warnWords);  
    badWordsSet = new Set(badWords);  
    enhancedBadWordsSet = new Set(enhancedBadWords);  
}
window.onload = function() {  
    init().catch(console.error);
    document.querySelector("#notice-input").focus();
}

function check_notice() {
    
    document.querySelector("#results").innerHTML = "请稍候...";
    async function main() {  
        let inputStr = document.querySelector("#notice-input").value;  
    
        function parseText(text, step = 2) {  
            const result = [];  
            var temp = "";
            for (let i = 0; i < text.length; i++) {  
                for (let j = i; j < i + step && j < text.length; j++) {  
                    temp += text[j];
                    result.push(temp);  
                }
                temp = "";  
            }  
            result.push(text[text.length - 1]);  
            return result;  
        }  
    
        function setInvalidStorage(invalidStorage, position, char, length = 1) {  
            for (let i = position; i < position + length; i++) {  
                if (!(i in invalidStorage)) {  
                    invalidStorage[i] = [char];  
                } else {  
                    invalidStorage[i].push(char);  
                }  
            }  
        }  
    
        function sliceInvalidChar(text) {  
            const invalidChars = [',', '.', '!', '?', ':', ';', '，', '。', '！', '？', '：', '；', '\n', ' ', '/', '"', "'", '、', '‘', '’', '“', '”', '(', ')', '（', '）'];  
            const invalidStorage = {};  
            let position = 0;  
            let newText = "";  
            let i = 0; // 使用 index 变量来遍历文本

            while (i < text.length) {
                const char = text[i];
                // 使用 codePointAt 检查字符是否是 emoji
                const codePoint = char.codePointAt(0);
                if (codePoint > 0xFFFF) {
                    // 如果是 emoji，直接添加到 newText
                    newText += char;
                    position++;
                    i+=2; // emoji 通常占用两个字符
                } else if (invalidChars.includes(char)) {  
                    setInvalidStorage(invalidStorage, position, char);  
                    i++; // 继续检查下一个字符
                } else {  
                    newText += char;  
                    position++;  
                    i++; // 继续检查下一个字符  
                }  
            }  
            return [newText, invalidStorage];  
        }

    
        function restoreInvalidChar(text, invalidStorage) {  
            let bad = false;  
            let accept = false;  
            let warn = false;  
            let enhance = false;  
            let newText = "";  
            text += " ";
            for (let position = 0; position < text.length; position++) {  
                
                if (position in invalidStorage) {  
                    // 先统计出现2的次数
                    var cnt = 0, index = 0;
                    for (var i = 0; i < invalidStorage[position].length; i++) {  
                        if (invalidStorage[position][i] == "2"){
                            cnt ++;
                            index = i;
                        }
                    }
                    if (cnt == 1) {  //  // 至少要双向通过才算，因此移除"2"
                        invalidStorage[position].splice(index, 1);
                    }

                    let minChar = "9", minCharCnt = 0;  
                    for (const char of invalidStorage[position]) {  
                        if (char >= '0' && char <= '9') {  
                            if (char < minChar) {  
                                minChar = char;  
                                minCharCnt = 1;  
                            } else if (char == minChar) {  
                                minCharCnt++;  
                            }  
                        } else {  
                            newText += "</span>" + char;  
                            bad = false;  
                            accept = false;  
                            warn = false;  
                            enhance = false;  
                        }  
                    }  
                    if (minChar === "1" && !bad) {  
                        if (accept || warn || enhance) {  
                            newText += '</span>';  
                            accept = false;  
                            warn = false;  
                            enhance = false;  
                        }  
                        newText += '<span class="bad" style="background-color:pink;border-radius:5px" title="95%可能是违禁词。根据用户提交违禁词验证得到，一般真实有效" onclick="alert(this.title)">';  
                        bad = true;  
                    } else if (minChar === "2" && !accept) {  
                        if (bad || warn || enhance) {  
                            newText += '</span>';  
                            bad = false;  
                            warn = false;  
                            enhance = false;  
                        }  
                        newText += '<span class="accept" style="background-color:aquamarine;border-radius:5px" title="95%可能是没问题的内容。收集近两周通过的公告筛选得到，一般没问题" onclick="alert(this.title)">';  
                        accept = true;  
                    } else if (minChar === "3" && !warn) {  
                        if (bad || accept || enhance) {  
                            newText += '</span>';  
                            bad = false;  
                            accept = false;  
                        }  
                        newText += '<span class="warn" style="background-color:yellow;border-radius:5px" title="这是疑似违禁词，大约10%可能性。收集以前被清空过的公告，可能含有违禁词，但准确性不高" onclick="alert(this.title)">';  
                        warn = true;  
                    } else if (minChar === "0" && !enhance) {  
                        if (bad || accept || warn) {  
                            newText += '</span>';  
                            bad = false;  
                            accept = false;  
                            warn = false;  
                        }  
                        newText += '<span class="enhance" style="background-color:orange;border-radius:5px" title="这是通用违禁词，大约30%可能性。收集坚果墙等等通用违禁词库，范围广但容易误报" onclick="alert(this.title)">';  
                        enhance = true;  
                    } else if (minChar === "9" && (bad || accept || warn || enhance)){
                        newText += '</span>';  
                        bad = false;  
                        accept = false;  
                        warn = false;  
                        enhance = false;  
                    }
                }  
                else if (bad || accept || warn || enhance) {  
                    newText += '</span>';  
                    bad = false;  
                    accept = false;  
                    warn = false;  
                    enhance = false;  
                }  
                newText += text[position];  
                
            }  
            
            return newText;  
        }  
    
        var [validInputStr, invalidStorage] = sliceInvalidChar(inputStr);  
    
        const textSet = new Set(parseText(validInputStr));  
        const textSetLong = new Set(parseText(validInputStr, 4));  
    
        var matchedList = [];  
    
        // 匹配bad_words  
        const textBadSet = new Set([...badWordsSet].filter(word => textSetLong.has(word) || word[0] == '/' || word.length > 4 || word.includes('|')));  
        // console.log(textBadSet);  
        for (const pattern of textBadSet) {  
            let tempValidInputStr = validInputStr;  
            let pos = 0;  
            if (pattern[0] == '/') { // 正则表达式  
                var exp = new RegExp(pattern.slice(1,-1), "g");  
                var match = tempValidInputStr.match(exp);  
                // console.log(exp);
                // console.log(match);  
                var length = 0;  
                if (!match)  
                    continue;  
                for (var i = 0; i < match.length; i++) {  
                    pos += tempValidInputStr.indexOf(match[i]);  
                    length = match[i].length;  
                    tempValidInputStr = validInputStr.slice(pos + length);  
                    setInvalidStorage(invalidStorage, pos, "1", length);  
                    matchedList.push(match[i]);  
                    pos += length;  
                }  
            } else if (pattern.includes('|')) {
                var multiple_valid = true;  
                var words = pattern.split('|');  
                for (var i = 0; i < words.length; i++) {  
                    if (!tempValidInputStr.includes(words[i])) {
                        multiple_valid = false;  
                        break;
                    }
                }
                if (multiple_valid) {
                    matchedList.push(pattern);  
                    for (var subpattern of words) { 
                        // console.log(subpattern);
                        if (subpattern == "") {continue;}

                        tempValidInputStr = validInputStr;
                        pos = 0;
                        while (tempValidInputStr.includes(subpattern)) {  
                            pos += tempValidInputStr.indexOf(subpattern);  
                            tempValidInputStr = validInputStr.slice(pos + subpattern.length);  
                            setInvalidStorage(invalidStorage, pos, "1", subpattern.length);  
                            pos += subpattern.length;  
                        }  
                    }
                } 
            } else {
                while (tempValidInputStr.includes(pattern)) {  
                    pos += tempValidInputStr.indexOf(pattern);  
                    tempValidInputStr = validInputStr.slice(pos + pattern.length);  
                    setInvalidStorage(invalidStorage, pos, "1", pattern.length);  
                    matchedList.push(pattern);  
                    pos += pattern.length;  
                }  
            }
        }  

        if (document.querySelector("#enhanced-check").checked) {  
            // 匹配enhanced_bad_words  
            const textEnhancedBadSet = new Set([...enhancedBadWordsSet].filter(word => textSetLong.has(word) || word[0] == '/' || word.length > 4 || word.includes('|')));  
            // console.log(textEnhancedBadSet);  
            for (const pattern of textEnhancedBadSet) {  
                let tempValidInputStr = validInputStr;  
                let pos = 0;  
                if (pattern[0] == '/') { // 正则表达式  
                    var exp = new RegExp(pattern.slice(1,-1), "g");  
                    var match = tempValidInputStr.match(exp);  
                    var length = 0;  
                    if (!match)      
                        continue;  
                    for (var i = 0; i < match.length; i++) {  
                        pos += tempValidInputStr.indexOf(match[i]);  
                        length = match[i].length;  
                        tempValidInputStr = validInputStr.slice(pos + length);  
                        setInvalidStorage(invalidStorage, pos, "0", length);  
                        matchedList.push(match[i]);  
                        pos += length;  
                    }  
                } else if (pattern.includes('|')) {
                    var multiple_valid = true;  
                    var words = pattern.split('|');  
                    for (var i = 0; i < words.length; i++) {  
                        if (!tempValidInputStr.includes(words[i])) {
                            multiple_valid = false;  
                            break;
                        }
                    }
                    if (multiple_valid) {
                        matchedList.push(pattern);  
                        for (var subpattern of words) { 
                            if (subpattern == "") {continue;}
                            tempValidInputStr = validInputStr;   
                            pos = 0;
                            while (tempValidInputStr.includes(subpattern)) {  
                                pos += tempValidInputStr.indexOf(subpattern);  
                                tempValidInputStr = validInputStr.slice(pos + subpattern.length);  
                                setInvalidStorage(invalidStorage, pos, "0", subpattern.length);  
                                pos += subpattern.length;  
                            }  
                        }
                    } 
                } else {
                    while (tempValidInputStr.includes(pattern)) {  
                        pos += tempValidInputStr.indexOf(pattern);  
                        tempValidInputStr = validInputStr.slice(pos + pattern.length);  
                        setInvalidStorage(invalidStorage, pos, "0", pattern.length);  
                        matchedList.push(pattern);  
                        pos += pattern.length;  
                    }  
                }
            }  
        }
    
        // 匹配accept_words  
        const textAcceptSet = new Set([...textSet].filter(word => acceptWordsSet.has(word)));  
        // console.log(textSet);  
        // console.log(textAcceptSet);  
        for (const word of textAcceptSet) {  
            let tempValidInputStr = validInputStr;  
            let pos = 0;  
            while (tempValidInputStr.includes(word)) {  
                pos += tempValidInputStr.indexOf(word);  
                tempValidInputStr = validInputStr.slice(pos + word.length);  
                setInvalidStorage(invalidStorage, pos, "2", word.length);  
                pos += word.length;  
            }  
        }  
    
        // 匹配warn_words  
        const textWarnSet = new Set([...textSet].filter(word => warnWordsSet.has(word)));  
        // console.log(textWarnSet);  
        for (const word of textWarnSet) {  
            let tempValidInputStr = validInputStr;  
            let pos = 0;  
            while (tempValidInputStr.includes(word)) {  
                pos += tempValidInputStr.indexOf(word);  
                tempValidInputStr = validInputStr.slice(pos + word.length);  
                setInvalidStorage(invalidStorage, pos, "3", word.length);  
                pos += word.length;  
            }  
        }  
        // 转义\n为<br>  
        var result = restoreInvalidChar(validInputStr, invalidStorage).replace(/\n/g, "<br>");  
        document.querySelector("#results").innerHTML = result;
        if (matchedList.length === 0) {  
            matchedList.push("无");  
        }  
        document.querySelector("#matches").innerHTML = "匹配到的词汇：" + matchedList.join(", ");  
    }  
    
    main().catch(
        function(error) {  
            console.error(error);  
            document.querySelector("#results").innerHTML = "出错了，请刷新网页或更换浏览器~还不行请联系麦花<br>错误信息：" + error.message;  
        }  
    );
    
}