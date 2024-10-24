
async function fetchJson(url) {  
    return await fetch(url)  
       .then(response => response.json())  
       .then(data => {  
            return data;  
        })  
       .catch(error => {  
            console.error(error);  
        });  
}  

const acceptWordsUrl = "/assets/accept_words.json";  
const badWordsUrl = "/assets/bad_words.json";  
const enhancedBadWordsUrl = "/assets/enhanced_bad_words.json";
const warnWordsUrl = "/assets/warn_words.json"; 

let badWords, enhancedBadWords, acceptWords, warnWords;  
let acceptWordsSet, warnWordsSet;  
async function init() {  
    [badWords, acceptWords, enhancedBadWords, warnWords] = await Promise.all([  
        fetchJson(badWordsUrl),  
        fetchJson(acceptWordsUrl),  
        fetchJson(enhancedBadWordsUrl),
        fetchJson(warnWordsUrl)  
    ]);  
    acceptWordsSet = new Set(acceptWords);  
    warnWordsSet = new Set(warnWords);  
}
init().catch(console.error);
window.onload = function() {  
    document.querySelector("#notice-input").focus();
}

function check_notice() {
    
    document.querySelector("#results").innerHTML = "请稍候...";
    async function main() {  
        let inputStr = document.querySelector("#notice-input").value;  
    
        function parseText(text) {  
            const result = [];  
            for (let i = 0; i < text.length - 1; i++) {  
                result.push(text[i]);  
                result.push(text[i] + text[i + 1]);  
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
            for (let position = 0; position < text.length; position++) {  
                if (position in invalidStorage) {  
                    let minChar = "9";  
                    for (const char of invalidStorage[position]) {  
                        if (char >= '0' && char <= '9') {  
                            if (char < minChar) {  
                                minChar = char;  
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
                        newText += '<span class="warn" style="background-color:lemonchiffon;border-radius:5px" title="这是疑似违禁词，大约10%可能性。收集以前被清空过的公告，可能含有违禁词，但准确性不高" onclick="alert(this.title)">';  
                        warn = true;  
                    } else if (minChar === "0" && !enhance) {  
                        if (bad || accept || warn) {  
                            newText += '</span>';  
                            bad = false;  
                            accept = false;  
                            warn = false;  
                        }  
                        newText += '<span class="enhance" style="background-color:orange;border-radius:5px" title="这是通用违禁词，大约30%可能性。收集近两周通过的公告筛选得到，可能含有违禁词，但准确性较高" onclick="alert(this.title)">';  
                        enhance = true;  
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
    
        var matchedList = [];  
    
        // 匹配bad_words  
        for (const pattern of badWords) {  
            let tempValidInputStr = validInputStr;  
            let pos = 0;  
            while (tempValidInputStr.includes(pattern)) {  
                pos += tempValidInputStr.indexOf(pattern);  
                tempValidInputStr = validInputStr.slice(pos + pattern.length);  
                setInvalidStorage(invalidStorage, pos, "1", pattern.length);  
                matchedList.push(pattern);  
                pos += pattern.length;  
            }  
        }  
        if (document.querySelector("#enhanced-check").checked) {  
            // 匹配enhanced_bad_words  
            for (const pattern of enhancedBadWords) {  
                let tempValidInputStr = validInputStr;  
                let pos = 0;  
                while (tempValidInputStr.includes(pattern)) {  
                    pos += tempValidInputStr.indexOf(pattern);  
                    tempValidInputStr = validInputStr.slice(pos + pattern.length);  
                    setInvalidStorage(invalidStorage, pos, "0", pattern.length);  
                    matchedList.push(pattern);  
                    pos += pattern.length;  
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
        document.querySelector("#warn").style.display = "block";  
        var result = restoreInvalidChar(validInputStr, invalidStorage).replace(/\n/g, "<br>");  
        document.querySelector("#results").innerHTML = result;
        if (matchedList.length === 0) {  
            matchedList.push("无");  
        }  
        document.querySelector("#matches").innerHTML = "匹配到的词汇：" + matchedList.join(", ");  
    }  
    
    main().catch(console.error);
    
}