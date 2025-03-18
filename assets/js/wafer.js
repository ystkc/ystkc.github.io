let currentSearchText = "";
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
  const input_text = document.getElementById("searchInput").value;
  if (text === "" || input_text !== "") { // 非数字或空字符串  || !/^\d+$/.test(text)
    text = input_text;
  } else document.getElementById("searchInput").value = text;
  search(text);
}


function checkPasteBoard() {
  if (document.getElementById("searchInput").value !== "") {
    console.log(1);processText("");
  }
  // 尝试从剪贴板获取内容
  try {
    // 现代浏览器方案
    navigator.clipboard.readText().then((text) => {
      console.log(2);processText(text);
    });
  } catch (err1) {
    try {
      // 替代方案1
      const text = window.clipboardData.getData('text');
      if (text) {
        console.log(3);processText(text);
      } else throw new Error(`Empty`);
    } catch (err2) {
      try {
        // 替代方案2
        const searchInput = document.getElementById("searchInput");
        searchInput.focus();
        document.execCommand('paste');
        const text = searchInput.value.trim();
        if (text) {
          console.log(4);processText(text);
        } else throw new Error("Empty"); // 没有办法了，提示用户手动粘贴内容
      } catch (err3) {
        try {
          alert(`您的浏览器不支持访问剪贴板，请手动粘贴内容 或用新版Chrome/Edge浏览器 (${err1}|${err2}|${err3})`);
          console.log(5);processText("");
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
  url = window.location.origin + '/';
  [blacklist, blacklistString] = await Promise.all([
    biscuitsToDict(await fetchBinAndUnzip(url + blacklistAssets, 1, 2, false)),
    fetchBinAndUnzip(url + blacklistStringAssets, 2, 2, false),
  ]);
  if (blacklist === undefined || blacklistString === undefined) {
    initStatus = -1;
    return;
  }
  // 将blacklist中每个条目的1、5项转为日期字符串，储存到blacklistString中
  let blacklistStringLen = blacklistString.length;
  function replace_date(index, sub_index, item_index) {
    let date_str = new Date(blacklist[index][sub_index][item_index]*1000).toLocaleString();
    blacklistString.push(date_str);
    blacklist[index][sub_index][item_index] = blacklistStringLen;
    blacklistStringLen++;
  }
  for (const key of Object.keys(blacklist)) {
    for (let j = 0; j < blacklist[key].length; j++) {
      replace_date(key, j, 1);
      replace_date(key, j, 5);
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
      for (const key of Object.keys(blacklist)) cnt += blacklist[key].length;
      return cnt;
    }
    document.getElementById("date").textContent = blacklistString[0] + ',共' + cnt_blacklist() + '条数据';
    document.getElementById("result").parentNode.classList.remove("item"); // 防止result过长导致透明度变化
    fadeController.reinit();
    // 绑定enter事件
    document.addEventListener("keyup", function (event) {
        if (event.key === 'Enter') {
          event.preventDefault();
          document.getElementById("searchBtn").click();
        }
    });
  }
};
function display_cnt(result_cnt, total_cnt, timeStart) {
  const timeEnd = performance.now();
  const timeCost = timeEnd - timeStart;
  document.getElementById("result-cnt").textContent = `共找到 ${total_cnt} 条结果，已展示 ${result_cnt} 条，耗时 ${timeCost.toFixed(0)}ms`;
}
function search(input) { // string
  if (currentSearchText === input) return; // 避免重复搜索
  currentSearchText = input;
  const timeStart = performance.now();
  document.getElementById("result").innerHTML = "正在查询...";
  if (input === "") {
      document.getElementById("result").innerHTML = "请输入要查询的信息！";
      return;
  }
  function get_summary(input) {
    if (input.length > 10) return `<span class='skyblue'>${input.slice(0, 10)}</span>...`;
    else return input; // 如果完整显示，则无需加span，因为后面会统一替换
  }
  let input_int = parseInt(input);
  // 先查询id
  let results_showed = 0, result_not_showed = 0, result_str = `${get_summary(input)}的查询结果：<br>`;
  const results = blacklist[input_int];
  function format_result(key, result) {
    let reason="";
    for (const index of result[2]) reason += `<span class='lightgrey'>${blacklistString[index]}</span> `;
    return `<div class='result wheat'>
<p>id: ${key}</p>
<p>昵称: ${blacklistString[result[0]]}</p>
<p>记录日期: ${blacklistString[result[1]]}</p>
<p>原因: ${reason}</p>
<p>记录人: ${blacklistString[result[3]]}</p>
<p>备注: ${blacklistString[result[4]]}</p>
<p>最后编辑时间: ${blacklistString[result[5]]}</p>
<p>最后编辑人: ${blacklistString[result[6]]}</p>
<p>首次编辑人: ${blacklistString[result[7]]}</p>
</div>`;
  }
  if (results !== undefined) {
      // id: [nickname, date(timestamp), reason, recorder, remark, last_edit_time(timestamp), last_editor, first_editor]
      for (const result of results) {
        if (results_showed > 100) {
          result_not_showed ++;
          continue;
        } else results_showed++;
        result_str += format_result(input, result);
      }
  }
  
  // 从blacklistString中搜索
  const matched_blacklist_string = new Set();
  const matched_index = []; // index
  const matched_sub_index = []; // [index, sub_index]
  for (let i = 0; i < blacklistString.length; i++) {
    if (blacklistString[i].includes(input)) {
      matched_blacklist_string.add(i);
    }
  }
  if (matched_blacklist_string.size > 0) {
    // 从blacklist.keys中搜索（包含子串）
    for (let key of Object.keys(blacklist)) { // int
      if (key.toString().includes(input)) {
        if (key !== input_int)matched_index.push(key);
        continue; // 避免重复添加
      }
      const items = blacklist[key];
      for (let j = 0; j < items.length; j++) {
        for (const sub_item of items[j]) {
          // 如果是列表，则遍历列表
          if (Array.isArray(sub_item)) {
            let matched = false;
            for (const index of sub_item) {
              if (matched_blacklist_string.has(index)) {
                matched_sub_index.push([key, j]);
                matched = true;
                break;
              }
            }
            if (matched) break;
          } else if (matched_blacklist_string.has(sub_item)) {
            matched_sub_index.push([key, j]);
            break;
          }
        }
      }
    }
  }
  for (const key of matched_index) {
    for (const sub_item of blacklist[key]) {
      if (results_showed > 100) {
        result_not_showed ++;
        continue;
      } else results_showed++;
      result_str += format_result(key, sub_item);
    }
  }
  for (const key_sub of matched_sub_index) {
    if (results_showed > 100) {
      result_not_showed ++;
      continue;
    } else results_showed++;
    result_str += format_result(key_sub[0], blacklist[key_sub[0]][key_sub[1]]);
  }
  if (results_showed === 0) {
    result_str += "未找到相关记录！";
  }
  result_str = result_str.replaceAll(input, `<span class='skyblue'>${input}</span>`);
  document.getElementById("result").innerHTML = result_str;
  display_cnt(results_showed, results_showed + result_not_showed, timeStart);
}