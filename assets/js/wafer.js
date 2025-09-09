let currentSearchText = "";
function encoder(array, no_convert = false) {
  const byteArray = new Uint8Array(array);
  let result = [];
  let index = 0;
  for (let i = 0; i < byteArray.length; i++, index++) {
    // 将其中的,,替换成,[],（节省传输字节）或\n\n同理
    const byteA = result[index - 1];
    const byteB = byteArray[i] ^ 0x1f;
    if ((byteA == 44 && byteB == 44) || (byteA == 10 && byteB == 10)) {
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

const blacklistAssets = "assets/blacklist.bin.zip";

let blacklist,
  searchString = [];
let initStatus = 0;
function processText(text) {
  text = text.trim();
  const input_text = document.getElementById("searchInput").value;
  if (text === "" || input_text !== "") {
    // 非数字或空字符串  || !/^\d+$/.test(text)
    text = input_text;
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
      const text = window.clipboardData.getData("text");
      if (text) {
        processText(text);
      } else throw new Error(`Empty`);
    } catch (err2) {
      try {
        // 替代方案2
        const searchInput = document.getElementById("searchInput");
        searchInput.focus();
        document.execCommand("paste");
        const text = searchInput.value.trim();
        if (text) {
          processText(text);
        } else throw new Error("Empty"); // 没有办法了，提示用户手动粘贴内容
      } catch (err3) {
        try {
          alert(
            `您的浏览器不支持访问剪贴板，请手动粘贴内容 或用新版Chrome/Edge浏览器 (${err1}|${err2}|${err3})`
          );
          processText("");
        } catch (err4) {
          alert(err4);
        }
      }
    }
  }
}

function handlePaste(e) {
  setTimeout(() => {
    processText("");
  }, 100);
}
async function init() {
  url = window.location.origin + "/";
  [blacklist] = await Promise.all([
    await fetchBinAndUnzip(url + blacklistAssets, 1, 1, true),
  ]);
  if (blacklist === undefined) {
    initStatus = -1;
    return;
  }
  // 将blacklist中每个条目的1、3、8项转为日期字符串，第4改为原因，9改为表名
  const reasonDict = blacklist[-1];
  const tableDict = blacklist[-2];
  function to_date(value) {
    return new Date(value * 1000).toLocaleString();
  }
  function interpretR(reason) {
    let reason_ids = reason.split(",");
    let reason_strs = [];
    for (const index of reason_ids)
      reason_strs.push(reasonDict[parseInt(index)]);
    return reason_strs;
  }
  for (const key of Object.keys(blacklist)) {
    if (key <= 0) continue;
    for (let j = 0; j < blacklist[key].length; j++) {
      blacklist[key][j][1] = to_date(blacklist[key][j][1]);
      blacklist[key][j][3] = to_date(blacklist[key][j][3]);
      blacklist[key][j][8] = to_date(blacklist[key][j][8]);
      blacklist[key][j][4] = interpretR(blacklist[key][j][4]);
      blacklist[key][j][9] = tableDict[blacklist[key][j][9]];
      // 将blacklist[key][j]中的所有值连接成字符串，用于搜索
      if (searchString[key] === undefined) searchString[key] = [];
      searchString[key][j] = blacklist[key][j].join("\n");
    }
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

    function cnt_blacklist() {
      let cnt = 0;
      for (const key of Object.keys(blacklist)) {
        if (key <= 0) continue;
        cnt += blacklist[key].length;
      }
      return cnt;
    }
    document.getElementById("date").textContent =
      "更新于" + blacklist[0] + ",共" + cnt_blacklist() + "条数据";
    document.getElementById("result").parentNode.classList.remove("item"); // 防止result过长导致透明度变化
    fadeController.reinit();
    // 绑定enter事件
    document.addEventListener("keyup", function (event) {
      if (event.key === "Enter") {
        event.preventDefault();
        document.getElementById("searchBtn").click();
      }
    });
  }
};
function display_cnt(result_cnt, total_cnt, timeStart) {
  const timeEnd = performance.now();
  const timeCost = timeEnd - timeStart;
  document.getElementById(
    "result-cnt"
  ).textContent = `共找到 ${total_cnt} 条结果，已展示 ${result_cnt} 条，耗时 ${timeCost.toFixed(
    0
  )}ms`;
}
function search(input) {
  input = input.trim();
  if (currentSearchText === input) return; // 避免重复搜索
  document.getElementById("result").innerHTML = "正在查询...";
  if (input === "") {
    document.getElementById("result").innerHTML = "请输入要查询的信息！";
    return;
  }
  currentSearchText = input;
  const timeStart = performance.now();
  function get_summary(input) {
    if (input.length > 10)
      return `<span class='skyblue'>${input.slice(0, 10)}</span>...`;
    else return input; // 如果完整显示，则无需加span，因为后面会统一替换
  }
  let results_showed = 0,
    result_not_showed = 0,
    result_str = `${get_summary(input)}的查询结果：<br>`;
  // 先查询id
  const results = blacklist[parseInt(input)];
  function demonReason(reason_strs) {
    let reason_dm = "";
    for (const str of reason_strs)
      reason_dm += `<span class='lightgrey'>${str}</span> `;
    return reason_dm;
  }
  function format_result(key, result) {
    return `<div class='result wheat'>
<p>id: ${key}</p>
<p>创建日期: ${result[1]}</p>
<p>昵称: ${result[2]}</p>
<p>退班时间: ${result[3]}</p>
<p>拉黑原因: ${demonReason(result[4])}</p>
<p>记录人: ${result[5]}</p>
<p>记录人QQ: ${result[6]}</p>
<p>备注: ${result[7]}</p>
<p>最后编辑时间: ${result[8]}</p>
<p>表名: ${result[9]}</p>
</div>`;
  }

  // 从searchString中搜索
  for (const key of Object.keys(searchString)) {
    for (let j = 0; j < searchString[key].length; j++) {
      if (searchString[key][j].includes(input)) {
        if (results_showed > 100) {
          result_not_showed++;
          continue;
        } else results_showed++;
        result_str += format_result(key, blacklist[key][j]);
      }
    }
  }
  if (results_showed === 0) {
    result_str += "未找到相关记录！";
  }
  result_str = result_str.replaceAll(
    input,
    `<span class='skyblue'>${input}</span>`
  );
  document.getElementById("result").innerHTML = result_str;
  display_cnt(results_showed, results_showed + result_not_showed, timeStart);
}
