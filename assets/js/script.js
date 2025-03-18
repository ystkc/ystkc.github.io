function encoder(array, no_convert = false) {
  const byteArray = new Uint8Array(array);
  var result = [];
  var index = 0;
  for (let i = 0; i < byteArray.length; i++, index++) {
    // 将其中的,,替换成,[],（节省传输字节）
    if (result[index - 1] == 44 && (byteArray[i] ^ 0x1f) == 44) {
      result.push(91);
      result.push(93);
      index += 2;
    }
    result.push(byteArray[i] ^ 0x1f);
  }
  if (no_convert) return result;
  const processedArray = new Uint8Array(result);
  return new TextDecoder("utf-8").decode(processedArray);
}

async function fetchBin(url, index, total) {
  return await fetch(url.replace(".zip", ""))
    .then((response) => {
      if (!response.ok) {
        // throw new Error(`网络错误: ${response.status} ${response.statusText}`);
      }
      return response.arrayBuffer();
    })
    .then((data) => {
      document.querySelector(
        "#results"
      ).innerHTML += `第 ${index}/${total} 个词库加载完成！<br>`;
      return JSON.parse(encoder(data));
    })
    .catch((error) => {
      console.error(error);
      document.querySelector(
        "#results"
      ).innerHTML += `加载备份JSON时发生错误: ${error.message}<br>`;
    });
}
async function fetchBinAndUnzip(url, index, total, is_json = true) {
  // document.querySelector("#results").innerHTML += `正在加载第 ${index} / ${total} 个词库，请稍候...<br>`;

  return await fetch(url)
    .then((response) => {
      if (!response.ok) {
        // 处理404错误或其他HTTP错误，抛出一个错误
        throw new Error(`网络错误: ${response.status} ${response.statusText}`);
      }
      return response.arrayBuffer();
    })
    .then((data) => {
      const zip = new JSZip();
      return zip
        .loadAsync(data) // 直接使用 ArrayBuffer
        .then((zip) => {
          const files = Object.keys(zip.files);
          const file = files[0];
          return zip.file(file).async("arraybuffer");
        })
        .then((data) => {
          document.querySelector(
            "#results"
          ).innerHTML += `第 ${index}/${total} 个词库加载完成！<br>`;
          document.querySelector(
            "#notice-input"
          ).value += `\n第 ${index}/${total} 个词库加载完成！`;
          if (is_json) {
            return JSON.parse(encoder(data));
          } else {
            return encoder(data).split("\n");
          }
        });
    })
    .catch((error) => {
      console.error(error);
      // document.querySelector("#results").innerHTML += `加载第 ${index} 个词库时发生错误: ${error.message}<br>`;
      // 可能没有zip，直接请求binary文件
      return fetchBin(url, index, total);
    });
}

let url;

const acceptWordsUrl = "assets/accept_words.bin.zip";
const badWordsUrl = "assets/bad_words.bin.zip";
const enhancedBadWordsUrl = "assets/enhanced_bad_words.bin.zip";
const warnWordsUrl = "assets/warn_words.bin.zip";

let badWords, enhancedBadWords, acceptWords, warnWords;
let acceptWordsSet, warnWordsSet, badWordsSet, enhancedBadWordsSet;
let initStatus = 0;
async function init() {
  url = window.location.href;
  [badWords, acceptWords, enhancedBadWords, warnWords] = await Promise.all([
    fetchBinAndUnzip(url + badWordsUrl, 1, 4),
    fetchBinAndUnzip(url + acceptWordsUrl, 2, 4, false),
    fetchBinAndUnzip(url + enhancedBadWordsUrl, 3, 4),
    fetchBinAndUnzip(url + warnWordsUrl, 4, 4, false),
  ]);
  if (
    badWords === undefined ||
    acceptWords === undefined ||
    enhancedBadWords === undefined ||
    warnWords === undefined
  ) {
    initStatus = -1;
    return;
  }

  acceptWordsSet = new Set(acceptWords.slice(1));
  warnWordsSet = new Set(warnWords);
  badWordsSet = new Set(badWords);
  enhancedBadWordsSet = new Set(enhancedBadWords);
  initStatus = 1;
}
window.onload = async function () {
  const initPromise = init().catch(console.error);

  await initPromise;
  if (initStatus === -1 || initStatus === 0) {
    document.querySelector("#notice-input").value =
      "词库加载失败！请刷新网页 或 更换浏览器。";
    document.querySelector("#results").innerHTML +=
      "词库加载失败！请刷新网页 或 更换浏览器。<br>";
  } else {
    document.querySelector("#notice-input").disabled = false;
    document.querySelector("#notice-input").value = "";
    document.querySelector("#results").innerHTML += "初始化完成！<br>";
    document.querySelector("#date").innerHTML = acceptWords[0];
    document.querySelector("#notice-input").focus();
  }
};

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
      // const invalidChars = [',', '.', '!', '?', ':', ';', '，', '。', '！', '？', '：', '；','\n',' ','/','"',"'",'、','‘','’','“','”','(',')','（','）','~','*','@','～','【','】','《','》','[',']','%','％']
      const pattern =
        /[^\w\d\u4e00-\u9fa5\u2700-\u27bf\u{1F650}-\u{1F67F}\u{1F600}-\u{1F64F}\u2600-\u26FF\u{1F300}-\u{1F5FF}\u{1F900}-\u{1F9FF}\u{1FA70}-\u{1FAFF}\u{1F680}-\u{1F6FF}\u{1F100}-\u{1F1FF}\u{1F200}-\u{1F2FF}]/u;

      const replaceMap = {
        一: "1",
        二: "2",
        三: "3",
        四: "4",
        五: "5",
        六: "6",
        七: "7",
        八: "8",
        九: "9",
        零: "0",
        壹: "1",
        贰: "2",
        叁: "3",
        肆: "4",
        伍: "5",
        陆: "6",
        柒: "7",
        捌: "8",
        玖: "9",
        两: "2",
        〇: "0",
      };
      const invalidStorage = {};
      let position = 0;
      let newText = "";
      let i = 0; // 使用 index 变量来遍历文本

      var char = "",
        doubleChar = false;
      while (i < text.length) {
        // 使用 codePointAt 检查字符是否是 emoji
        if (text.codePointAt(i) > 0xffff) {
          doubleChar = true;
          char = text[i] + text[i + 1];
        } else {
          doubleChar = false;
          char = text[i];
        }
        if (char.match(pattern)) {
          // 如果被正则表达式匹配，则执行
          setInvalidStorage(invalidStorage, position, char);
          i++; // 继续检查下一个字符
          if (doubleChar) position --; // 双字符的一点小问题
        } else if (char in replaceMap) {
          newText += replaceMap[char];
          setInvalidStorage(invalidStorage, position, char);
          position++;
          i++; // 继续检查下一个字符
        } else if (char >= "A" && char <= "Z") {
          newText += char.toLowerCase();
          setInvalidStorage(invalidStorage, position, char);
          position++;
          i++;
        } else {
          newText += char;
          position++;
          i++; // 继续检查下一个字符
        }
        if (doubleChar) {
          i++;
          position++;
        }
      }
      // console.log(newText);
      // console.log(invalidStorage);
      return [newText, invalidStorage];
    }

    function restoreInvalidChar(text, invalidStorage) {
      let bad = false;
      let accept = false;
      let warn = false;
      let enhance = false;
      var doubleChar = false;
      let newText = "";
      var temp_text = "";
      const replaceList = [
        "一",
        "二",
        "三",
        "四",
        "五",
        "六",
        "七",
        "八",
        "九",
        "零",
        "壹",
        "贰",
        "叁",
        "肆",
        "伍",
        "陆",
        "柒",
        "捌",
        "玖",
        "两",
        "〇",
      ];
      text += " ";
      for (
        var textPosition = 0, position = 0;
        textPosition < text.length;
        position++, textPosition++
      ) {
        if (text.codePointAt(textPosition) > 0xffff) {
          doubleChar = true;
          temp_text = text[textPosition] + text[textPosition + 1];
        } else {
          doubleChar = false;
          temp_text = text[textPosition];
        }

        if (position in invalidStorage) {
          // 先统计出现2的次数
          var cnt = 0,
            index = 0;
          for (var i = 0; i < invalidStorage[position].length; i++) {
            if (invalidStorage[position][i] == "c") {
              cnt++;
              index = i;
            }
          }
          let minChar = "z",
            minCharCnt = 0;
          if (cnt == 1) {
            //至少要双向通过才算，因此移除"c"
            invalidStorage[position].splice(index, 1); // 注释掉本行可以减少嫌疑词以提升观感，但会漏掉一些。暂无更优解
          } else if (cnt == 0) {
            // 原本有嫌疑词字典，但资源开销太高，因此使用低配版预测
            minChar = "d";
          }

          for (const char of invalidStorage[position]) {
            if (char >= "a" && char <= "z") {
              if (char < minChar) {
                minChar = char;
                minCharCnt = 1;
              } else if (char == minChar) {
                minCharCnt++;
              }
            } else if (
              replaceList.includes(char) ||
              (char >= "A" && char <= "Z")
            ) {
              temp_text = char;
            } else {
              newText += "</span>" + char;
              bad = false;
              accept = false;
              warn = false;
              enhance = false;
            }
          }
          if (minChar === "b" && !bad) {
            if (accept || warn || enhance) {
              newText += "</span>";
              accept = false;
              warn = false;
              enhance = false;
            }
            newText +=
              '<span class="bad pink" title="95%可能是违禁词。根据用户提交违禁词验证得到，一般真实有效" onclick="alert(this.title)">';
            bad = true;
          } else if (minChar === "c" && !accept) {
            if (bad || warn || enhance) {
              newText += "</span>";
              bad = false;
              warn = false;
              enhance = false;
            }
            newText +=
              '<span class="accept aquamarine" title="95%可能是没问题的内容。收集通过的公告筛选得到，一般没问题" onclick="alert(this.title)">';
            accept = true;
          } else if (minChar === "d" && !warn) {
            if (bad || accept || enhance) {
              newText += "</span>";
              bad = false;
              accept = false;
            }
            newText +=
              '<span class="warn yellow" title="这是疑似违禁词，大约10%可能性。收集以前被清空过的公告，可能含有违禁词，但准确性不高" onclick="alert(this.title)">';
            warn = true;
          } else if (minChar === "a" && !enhance) {
            if (bad || accept || warn) {
              newText += "</span>";
              bad = false;
              accept = false;
              warn = false;
            }
            newText +=
              '<span class="enhance orange" title="这是通用违禁词，大约30%可能性。收集坚果墙等等通用违禁词库，范围广但容易误报" onclick="alert(this.title)">';
            enhance = true;
          } else if (minChar === "z" && (bad || accept || warn || enhance)) {
            newText += "</span>";
            bad = false;
            accept = false;
            warn = false;
            enhance = false;
          }
        } else if (bad || accept || warn || enhance) {
          newText += "</span>";
          bad = false;
          accept = false;
          warn = false;
          enhance = false;
        }
        newText += temp_text;
        if (doubleChar) {
          textPosition++;
          position++;
        }
      }

      return newText;
    }

    var [validInputStr, invalidStorage] = sliceInvalidChar(inputStr);

    const textSet = new Set(parseText(validInputStr));
    const textSetLong = new Set(parseText(validInputStr, 4));

    var matchedList = [];

    function checkBadWords(validInputStr, patternSet, matchedList, type) {
      for (const pattern of patternSet) {
        let tempValidInputStr = validInputStr;
        let pos = 0;
        if (pattern[0] == "/") {
          // 正则表达式
          var exp = new RegExp(pattern.slice(1, -1), "g");
          var match = tempValidInputStr.match(exp);
          var length = 0;
          if (!match) continue;
          for (var i = 0; i < match.length; i++) {
            pos += tempValidInputStr.indexOf(match[i]);
            length = match[i].length;
            tempValidInputStr = validInputStr.slice(pos + length);
            setInvalidStorage(invalidStorage, pos, type, length);
            matchedList.push(match[i]);
            pos += length;
          }
        } else if (pattern.includes("|")) {
          var multiple_valid = true;
          var words = pattern.split("|");
          var pos_list = [],
            deleted_length = 0;
          for (var i = 0; i < words.length; i++) {
            var index = tempValidInputStr.indexOf(words[i]);
            if (index == -1) {
              multiple_valid = false;
              break;
            } else {
              tempValidInputStr = tempValidInputStr.slice(index);
              pos_list.push(deleted_length + index);
              deleted_length += index;
            }
          }
          if (multiple_valid) {
            matchedList.push(pattern);
            for (var i in pos_list) {
              setInvalidStorage(
                invalidStorage,
                pos_list[i],
                type,
                words[i].length
              );
            }
          }
        } else {
          while (tempValidInputStr.includes(pattern)) {
            pos += tempValidInputStr.indexOf(pattern);
            tempValidInputStr = validInputStr.slice(pos + pattern.length);
            setInvalidStorage(invalidStorage, pos, type, pattern.length);
            matchedList.push(pattern);
            pos += pattern.length;
          }
        }
      }
      return matchedList;
    }
    // 匹配bad_words
    const textBadSet = new Set(
      [...badWordsSet].filter(
        (word) =>
          textSetLong.has(word) ||
          word[0] == "/" ||
          word.length > 4 ||
          word.includes("|")
      )
    );
    matchedList = checkBadWords(validInputStr, textBadSet, matchedList, "b");

    if (document.querySelector("#enhanced-check").checked) {
      // 匹配enhanced_bad_words
      const textEnhancedBadSet = new Set(
        [...enhancedBadWordsSet].filter(
          (word) =>
            textSetLong.has(word) ||
            word[0] == "/" ||
            word.length > 4 ||
            word.includes("|")
        )
      );
      matchedList = checkBadWords(
        validInputStr,
        textEnhancedBadSet,
        matchedList,
        "a"
      );
    }

    // 匹配accept_words
    const textAcceptSet = new Set(
      [...textSet].filter((word) => acceptWordsSet.has(word))
    );
    for (const word of textAcceptSet) {
      let tempValidInputStr = validInputStr;
      let pos = 0;
      while (tempValidInputStr.includes(word)) {
        pos += tempValidInputStr.indexOf(word);
        tempValidInputStr = validInputStr.slice(pos + word.length);
        setInvalidStorage(invalidStorage, pos, "c", word.length);
        pos += word.length;
      }
    }

    // 匹配warn_words
    const textWarnSet = new Set(
      [...textSet].filter((word) => warnWordsSet.has(word))
    );
    for (const word of textWarnSet) {
      let tempValidInputStr = validInputStr;
      let pos = 0;
      while (tempValidInputStr.includes(word)) {
        pos += tempValidInputStr.indexOf(word);
        tempValidInputStr = validInputStr.slice(pos + word.length);
        setInvalidStorage(invalidStorage, pos, "d", word.length);
        pos += word.length;
      }
    }
    // 转义\n为<br>
    var result = restoreInvalidChar(validInputStr, invalidStorage).replace(
      /\n/g,
      "<br>"
    );
    document.querySelector("#results").innerHTML = result;
    if (matchedList.length === 0) {
      document.querySelector(
        "#matches"
      ).innerHTML = `<div>未找到违禁词！<br>可加麦花qq帮找：<span id='qq' style='background-color:pink;border-radius:5px'>1612162886</span>或微信<span id='wechat' style='background-color:pink;border-radius:5px'>lianwumaipian</span>(点击色块复制)<br>免费，有空就查，勿催哦<br>.<br></div>`;
      addCopyButton(document.querySelector("#qq"));
      addCopyButton(document.querySelector("#wechat"));
    } else {
      document.querySelector("#matches").innerHTML =
        "匹配到的词汇：" + matchedList.join(", ");
    }
  }

  main().catch(function (error) {
    console.error(error);
    document.querySelector("#results").innerHTML =
      "出错了，请刷新网页或更换浏览器~还不行请联系麦花<br>错误信息：" +
      error.message;
  });
}
