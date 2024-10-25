---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults
# bundle exec jekyll serve --livereload

layout: home
---
<meta charset="UTF-8">
<style>
body {
  font-family: 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji';
}
</style>
<body>
百词斩公告违禁词检查器<br>
Created by 半只橙 & Cereanilla麦花<br>


<textarea id="notice-input" placeholder="Paste your BCZ notice here..." style="width: 80%; height: 300px;"></textarea><br>
<button id="search-btn" onclick="check_notice()">Check</button>
<input checked type="checkbox" id="enhanced-check">加强词典
<div id="matches"></div>
<div id="warn"><span style="color:red;" id="warn">本工具与百词斩官方无关，违禁词为用户收集，结果仅供参考</span><br>若仍然找不到违禁词，请将你的公告【全文】发送到1612162886@qq.com</div><br>
<div>检查结果：<span style="background-color:pink;border-radius:5px" title="根据用户提交违禁词验证得到，一般真实有效" onclick="alert(this.title)">确定的违禁词汇</span>
<span style="background-color:orange;border-radius:5px" title="收集坚果墙等等通用违禁词库，范围更广，但很可能有误报" onclick="alert(this.title)">增强版违禁词汇</span>
<span style="background-color:aquamarine;border-radius:5px" title="收集近两周通过的公告筛选得到，一般没问题" onclick="alert(this.title)">没问题的内容</span>
<span style="background-color:yellow;border-radius:5px" title="收集以前被清空过的公告，可能含有违禁词，但准确性不高" onclick="alert(this.title)">疑似违禁</span></div>
<div id="results"></div>
<!-- <div id="url" style="display:none;">{{ site.baseurl }}</div> -->
<!-- jszip3.7.1 -->
<script src="{{ site.baseurl }}/assets/js/jszip.min.js"></script>
<script src="{{ site.baseurl }}/assets/js/script.js"></script>
<!-- <a target="_blank" href="http://mail.qq.com/cgi-bin/qm_share?t=qm_mailme&email=p5aRlpWWkZWfn5Hn1taJxMjK" style="text-decoration:none;">找不到违禁词？点我</a> -->
</body>
