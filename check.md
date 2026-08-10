---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults
# bundle exec jekyll serve --livereload

layout: sidebar
title: 公告违禁词检查
subtitle: .
trexflag: 1
---
<meta charset="UTF-8">
<style>
#salt-protect-dialog { max-width: 90vw; width: 760px; }
#salt-protect-text { max-height: 45vh; overflow: auto; padding: 8px; line-height: 2; white-space: pre-wrap; font-family: monospace; border: 1px solid #bbb; }
#salt-protect-text button { border: 0; padding: 2px 4px; margin: 1px; font: inherit; cursor: pointer; border-radius: 3px; }
#salt-protect-text .salt-protected { background: #ffbd69; outline: 1px solid #d67b00; }
#salt-protect-text .salt-start { background: #9fd0ff; outline: 2px solid #2678c8; }
#salt-protect-text .salt-free { background: transparent; }
#salt-protect-text .salt-free:hover { background: #d9ecff; }
#salt-choice-dialog small { margin-left: 6px; }
</style>
<body>
百词斩公告违禁词检查器<br>
Created by 半只橙 & Cereanilla麦花<br>
<div id="date" style="color:gray">构建中...</div>
<div id="reminder"></div>
<div class="t-rex-wrapper">
<div class="interstitial-wrapper" id="t-rex"></div>
<textarea id="notice-input" placeholder="Paste your BCZ notice here..." style="width: 80%; height: 300px;" disabled>正在加载词库...请稍候...</textarea>
<div id="notice-length" aria-live="polite">当前长度：0</div>
</div>

<script>
// 检查是否有小恐龙游戏访问权限
function hasTrexAccess() {
  return document.cookie.includes('trex_access=true');
}

// 如果没有访问权限，隐藏游戏相关元素
if (!hasTrexAccess()) {
  document.getElementById('t-rex').style.display = 'none';
  document.getElementById('reminder').style.display = 'none';
}
</script>
<br><span><button id="search-btn" class="btn" onclick="check_notice()">Check</button><button id="disperse-btn" class="btn" onclick="disperse_bad_words()" hidden>加盐</button><button id="salt-undo-btn" class="btn" onclick="undoSalt()" hidden>撤销加盐</button>加强词典<input checked type="checkbox" style="width: 30px; height: 30px;" id="enhanced-check"></span>
<dialog id="salt-choice-dialog"><form method="dialog"><button title="将识别到的词中间加上句号，并在末尾加上《望海潮》上阙" value="punctuate" class="salt-choice">聚盐</button><br><button title="排成2~9列竖排框线，保护区原样保留。" value="vertical" class="salt-choice">树盐</button><br><button title="按带声调拼音替换部分汉字为不同的同音字，保护区不替换。" value="homophone" class="salt-choice">铜盐</button><button value="cancel">取消</button></form></dialog>
<dialog id="salt-protect-dialog"><form method="dialog"><h3>编辑保护区</h3><p id="salt-protect-help">橙色是保护区。点击橙色可取消；点击普通字符两次，先定左边界、再定右边界，可新增保护区。</p><div id="salt-protect-text" tabindex="0"></div><label id="salt-ratio-wrap" hidden>替换比例 <input id="salt-ratio" type="number" min="0" max="1" step="0.05" value="0.3"></label><br><button value="apply">应用</button> <button value="cancel">取消</button></form></dialog>
<div id="matches"></div>
<div id="warn">本工具与百词斩官方无关，违禁词为用户收集<br><span style="color:red;" id="warn">使用本工具代表您确认自己的内容合法合规<br>如用于传播不良信息产生的包括但不限于封号的后果由您自负</span><br>
<div id="legend">详细检查结果：<span class="violet" title="根据用户提交违禁词验证得到，一般真实有效" onclick="alert(this.title)">确定的违禁词汇</span>
<span class="orange" title="收集坚果墙等等通用违禁词库，范围更广，但很可能有误报" onclick="alert(this.title)">增强版违禁词汇</span>
<span class="pink" title="单独能发出去，但如果与其他内容一起发送就可能发不出去" onclick="alert(this.title)">轻微违禁词汇</span>
<span class="yellow" title="收集以前被清空过的公告，可能含有违禁词，但准确性不高" onclick="alert(this.title)">疑似违禁</span>
<span class="aquamarine" title="收集近两周通过的公告筛选得到，一般没问题" onclick="alert(this.title)">没问题的内容</span></div>
<hr>
<div id="results"></div>
<hr>
<!-- jszip3.7.1 -->
<script src="{{ site.baseurl }}/assets/js/jszip.min.js"></script>
<script src="{{ site.baseurl }}/assets/js/pinyin-pro.min.js"></script>
<script src="{{ site.baseurl }}/assets/js/script.js"></script>
<!-- busuanzi寄咯@25.7.14 -->
<!-- <script async src="//busuanzi.ibruce.info/busuanzi/2.3/busuanzi.pure.mini.js"></script> -->
<span id="busuanzi_container_page_pv">本页总访问量<span id="busuanzi_value_page_pv"></span>次</span>
