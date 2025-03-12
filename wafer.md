---
layout: sidebar
title: 周中退班名单查询
subtitle: Cereanilla麦花
---
百词斩周中退班王者名单查询<br>
由于上次名单破坏较大，楚楚姐姐仍在努力根据群历史记录修复<br>此为目前的最新版本，可能有错漏仅供参考<br>
<span style="background-color:pink;border-radius:5px">数据由王者班长自行录入，仅供班长群内部使用，如有错误请联系录入者</span><br>
<div id="date" style="color:gray">构建中请稍候...</div>
<input type="checkbox" id="autoPaste" onclick="toggleAutoPaste()" checked>自动访问剪贴板<br>
<input type="digit" id="searchInput" placeholder="输入bczId..." value="构建中..." disabled>
<button id="searchBtn" class="btn" onclick="search(document.getElementById('searchInput').value.trim())" disabled>查询</button><br>
<div id="result"></div>
<!-- jszip3.7.1 -->
<script src="{{ site.baseurl }}/assets/js/jszip.min.js"></script>
<script src="{{ site.baseurl }}/assets/js/wafer.js"></script>
<script async src="//busuanzi.ibruce.info/busuanzi/2.3/busuanzi.pure.mini.js"></script>
<span id="busuanzi_container_page_pv">本页总访问量<span id="busuanzi_value_page_pv"></span>次</span>