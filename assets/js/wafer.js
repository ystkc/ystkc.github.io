function encoder(array, no_convert = false) {
    const byteArray = new Uint8Array(array);
    let result = [];
    let index = 0;
    for (let i = 0; i < byteArray.length; i++, index++) {
      // 将其中的,,替换成,[],（节省传输字节）或\n\n同理
      const byteA = result[index - 1];
      const byteB = byteArray[i] ^ 0x1f;
      if (byteA == 44  && byteB == 44 || byteA == 10 && byteB == 10) {
        result.push(91);
        result.push(93);
        index += 2;
      }
      result.push(byteB);
    }
    if (no_convert) return result;
    const processedArray = new Uint8Array(result);
    return new TextDecoder("utf-8").decode(processedArray);
  }
  async function biscuitsToDict(biscuits) {
    // 将key\nvalue\nkey\nvalue\n...转化为{key:value, key:value, ...}的字典
    const dict = {};
    if (biscuits.length & 1)
        biscuits.pop(); // 去掉最后一个奇数位(可能是空字符串)
    for (let i = 0; i < biscuits.length; i += 2) {
        const key = biscuits[i].trim();
        let value = JSON.parse(biscuits[i + 1].trim());
        dict[key] = value;
    }
    return dict;
}
async function biscuitsToList(biscuits) {
    // 将value\nvalue\nvalue\n...转化为[value, value, ...]的列表
    const list = [];
    for (let i = 0; i < biscuits.length; i++) {
        const value = biscuits[i].trim();
        list.push(value);
    }
    return list;
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
          document.getElementById(
            "result"
          ).innerHTML += `第 ${index}/${total} 个表加载完成！<br>`;
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
    //   return fetchBin(url, index, total);
    });
}

const blacklistAssets = "assets/black_list.bin.zip";
const blacklistStringAssets = "assets/black_list_string.bin.zip";

let blacklist, blacklistString;
let initStatus = 0;
function processText(text) {
  text = text.trim();
  if (text === "" || !/^\d+$/.test(text)) { // 非数字或空字符串
    text = document.getElementById("searchInput").value;
  } else document.getElementById("searchInput").value = text;
  search(text);
}


function checkPasteBoard() {
  if (document.getElementById("searchInput").value !== "") {
    processText("");
  }
  // 尝试从剪贴板获取内容
  try {
    // 现代浏览器方案
    navigator.clipboard.readText().then((text) => {
      processText(text);
    });
  } catch (err1) {
    try {
      // 替代方案1
      const text = window.clipboardData.getData('text');
      if (text) {
        search(text);
      } else throw new Error(`Empty`);
    } catch (err2) {
      try {
        // 替代方案2
        const searchInput = document.getElementById("searchInput");
        searchInput.focus();
        document.execCommand('paste');
        const text = searchInput.value.trim();
        if (text) {
          search(text);
        } else throw new Error("Empty"); // 没有办法了，提示用户手动粘贴内容
      } catch (err3) {
        alert(`您的浏览器不支持访问剪贴板，请手动粘贴内容 或用新版Chrome/Edge浏览器 (${err1.message}|${err2.message}|${err3.message})`);
        processText("");
      }
    }
  }
}




function handlePaste(e) {
  const pastedText = e.clipboardData.getData('text/plain');
  if (pastedText) {
    processText(pastedText);
  }
}
async function init() {
  url = window.location.origin + '/';
  [blacklist, blacklistString] = await Promise.all([
    biscuitsToDict(await fetchBinAndUnzip(url + blacklistAssets, 1, 2, false)),
    fetchBinAndUnzip(url + blacklistStringAssets, 2, 2, false),
  ]);
  if (blacklist === undefined || blacklistString === undefined) {
    initStatus = -1;
    return;
  }
  initStatus = 1;
}
window.onload = async function () {
  const initPromise = init().catch(console.error);

  await initPromise;
  if (initStatus === -1 || initStatus === 0) {
    document.getElementById("date").innerHTML +=
      "词库加载失败！请刷新网页 或 更换浏览器。<br>";
      alert("词库加载失败！请刷新网页 或 更换浏览器。");
  } else {
    document.getElementById("searchInput").value = "";
    document.getElementById("searchInput").disabled = false;
    document.getElementById("searchInput").focus();
    document.getElementById("searchBtn").disabled = false;
    
    document.getElementById("date").textContent = blacklistString[0] + ',共' + Object.keys(blacklist).length + '条数据';
    // 绑定enter事件
    document.addEventListener("keyup", function (event) {
        if (event.key === 'Enter') {
          event.preventDefault();
          document.getElementById("searchBtn").click();
        }
    });
  }
};
function search(input) {
    document.getElementById("result").innerHTML = "正在查询...";
    if (input === "") {
        document.getElementById("result").innerHTML = "请输入要查询的id！";
        return;
    }
    const results = blacklist[input];
    setTimeout(() => {
      if (results === undefined) {
          document.getElementById("result").innerHTML = "未找到该id: " + input;
          return;
      } else {
          let result_str = "";
          // id: [nickname, date(timestamp), reason, recorder, remark, last_edit_time(timestamp), last_editor, first_editor]
          for (let result of results) {
            let reason = "";
            result_str += "<div class='result'>";
            for (let index of result[2]) {
                reason += "<span class='grey'>" + blacklistString[index] + "</span>";
            }
            result_str += `
                <p>id: ${input}</p>
                <p>昵称: ${blacklistString[result[0]]}</p>
                <p>记录日期: ${new Date(result[1]*1000).toLocaleString()}</p>
                <p>原因: ${reason}</p>
                <p>记录人: ${blacklistString[result[3]]}</p>
                <p>备注: ${blacklistString[result[4]]}</p>
                <p>最后编辑时间: ${new Date(result[5]*1000).toLocaleString()}</p>
                <p>最后编辑人: ${blacklistString[result[6]]}</p>
                <p>首次编辑人: ${blacklistString[result[7]]}</p>
            </div>`;
          }
          document.getElementById("result").innerHTML = result_str;
      }
    }, 500);
}