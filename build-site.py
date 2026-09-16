# -*- coding: utf-8 -*-
import io, re, os, shutil

import os as _os
BASE = _os.path.dirname(_os.path.abspath(__file__))
SITE = os.path.join(BASE, "site")

HEAD_CSS = '''<style>
body { margin:0; background:#cfe4e1; color:#10302b; font-family:"Noto Sans JP", system-ui, -apple-system, sans-serif; font-size:16px; line-height:1.8; -webkit-font-smoothing:antialiased; }
* { box-sizing:border-box; }
a { color:#1d7a72; }
a[style*="background:linear-gradient"]:hover, button:hover { filter:brightness(1.08); }
@keyframes marquee { from { transform:translateX(0); } to { transform:translateX(-50%); } }
@keyframes fadeUp { from { opacity:0; transform:translateY(18px); } to { opacity:1; transform:translateY(0); } }
@keyframes growX { from { transform:scaleX(0); } to { transform:scaleX(1); } }
@keyframes notifyDrop { 0% { opacity:0; transform:translateY(-140%); } 6% { opacity:1; transform:translateY(6%); } 9% { opacity:1; transform:translateY(0); } 46% { opacity:1; transform:translateY(0); } 56% { opacity:0; transform:translateY(-70%); } 100% { opacity:0; transform:translateY(-140%); } }
@keyframes pulseDot { 0%, 100% { transform:scale(1); opacity:1; } 50% { transform:scale(1.5); opacity:0.5; } }
@keyframes rowIn { 0%, 12% { opacity:0.35; } 22%, 100% { opacity:1; } }
@keyframes barGrow { from { width:0; } }
@keyframes popIn { from { opacity:0; transform:scale(0.85); } to { opacity:1; transform:scale(1); } }
section[id] { scroll-margin-top:72px; }
details summary::-webkit-details-marker { display:none; }
details summary { list-style:none; }
details.faq summary { position:relative; padding-right:32px; }
details.faq summary::after { content:"\FF0B"; position:absolute; right:0; top:19px; font-size:17px; font-weight:800; color:#1d7a72; line-height:1; }
details.faq[open] summary::after { content:"\FF0D"; }
:focus { outline:none; }
:focus-visible { outline:2px solid #1d7a72; outline-offset:2px; }
input:focus, select:focus { border-color:#1d7a72 !important; }
.sel { width:100%; font:inherit; font-size:16px; font-weight:500; padding:14px 40px 14px 16px; border:1px solid rgba(16,48,43,0.18); background-color:#eff8f6; color:#10302b; cursor:pointer; -webkit-appearance:none; appearance:none; background-image:url("data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='9' viewBox='0 0 14 9'%3E%3Cpath d='M1 1l6 6 6-6' fill='none' stroke='%231d7a72' stroke-width='2'/%3E%3C/svg%3E"); background-repeat:no-repeat; background-position:right 16px center; border-radius:0; }
.sel:invalid { color:#6d8d89; }
.bar-hidden { display:none; }
.hscroll { overflow-x:auto; -webkit-overflow-scrolling:touch; scrollbar-width:none; scroll-snap-type:x mandatory; }
.hscroll::-webkit-scrollbar { display:none; }
.nitte-embed { min-height:720px; width:100%; border:0; display:block; }
@media (max-width: 800px) { .nitte-embed { min-height:600px; } }
@media (prefers-reduced-motion: reduce) { * { animation:none !important; } }
</style>'''

def shell(title, desc, body, script=""):
    return '''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<meta name="description" content="%s">
<meta property="og:title" content="%s">
<meta property="og:description" content="%s">
<meta property="og:type" content="website">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;900&amp;display=swap">
%s
</head>
<body>
%s
%s
</body>
</html>
''' % (title, desc, title, desc, HEAD_CSS, body, script)

def inner(f):
    s = io.open(os.path.join(BASE,f), encoding="utf-8").read()
    b = s[s.index("<x-dc>")+6 : s.index("</x-dc>")]
    b = re.sub(r"<helmet>.*?</helmet>", "", b, flags=re.S)
    return b.strip()

lp, fm, tk = inner("index.html"), inner("form.html"), inner("thanks.html")

# --- sc-for（マーキー）展開 ---
tags = ['経営コンサルティング','SaaS・DXツール','資金調達支援','省エネ・電力切替','人材紹介・採用支援',
        'M&amp;A・事業承継','広告・PR・Web制作','オフィス設備・什器','研修・社員教育','不動産・店舗開発',
        '保険・士業サービス','福利厚生サービス']
tag_html = "".join('<div style="background:#fbfefd;border:1px solid #cfe4e1;border-radius:6px;padding:10px 20px;font-size:13px;font-weight:500;white-space:nowrap;color:#38534f">%s</div>' % t for t in tags*2)
lp = re.sub(r'<sc-for.*?</sc-for>', lambda m: tag_html, lp, flags=re.S)

# --- sc-if を素の要素へ ---
lp = lp.replace('<sc-if value="{{ profitOn }}" hint-placeholder-val="{{ false }}">', '<div class="figbody">')
lp = lp.replace('<sc-if value="{{ matrixOn }}" hint-placeholder-val="{{ false }}">', '<div class="figbody">')
lp = lp.replace('<sc-if value="{{ barVisible }}" hint-placeholder-val="{{ false }}">', '<div id="stickybar" class="bar-hidden">')
lp = lp.replace('</sc-if>', '</div>')

strip_hover = lambda s: re.sub(r'\s*style-hover="[^"]*"', '', s)
lp, fm, tk = map(strip_hover, (lp, fm, tk))

# --- ページ間リンクを実ファイルへ ---
def links(s):
    return (s.replace('href="W-Form.dc.html"', 'href="form.html"')
             .replace('href="W-LP.dc.html"',   'href="index.html"'))
lp, fm, tk = map(links, (lp, fm, tk))
lp = lp.replace('onSubmit="{{ handleSubmit }}"', 'id="wform"')
fm = fm.replace('onSubmit="{{ handleSubmit }}"', 'id="wform"')

assert not any(x in (lp+fm+tk) for x in ('sc-if','sc-for','{{','.dc.html','style-hover'))

LP_JS = '''<script>
(function(){
  var bar = document.getElementById('stickybar'), fv = document.getElementById('fv');
  var cf = document.getElementById('contact');
  function checkBar(){
    if(!bar||!fv) return;
    var nearForm = cf && cf.getBoundingClientRect().top < window.innerHeight - 60;
    bar.classList.toggle('bar-hidden', fv.getBoundingClientRect().bottom >= 0 || !!nearForm);
  }
  document.addEventListener('scroll', checkBar, { capture:true, passive:true });
  window.addEventListener('resize', checkBar);
  checkBar();
  // メニュー内のリンクを押したら閉じる
  document.addEventListener('click', function(e){
    var a = e.target.closest && e.target.closest('#menu a');
    var m = document.getElementById('menu');
    if (a && m) m.removeAttribute('open');
  });

  var lf = document.getElementById('wform');
  if (lf) {
    lf.addEventListener('submit', function(e){
      e.preventDefault();
      if (lf.checkValidity()) location.href = 'thanks.html';
      else lf.reportValidity();
    });
  }

  var figs = document.querySelectorAll('.figbody');
  Array.prototype.forEach.call(figs, function(el){ el.style.visibility = 'hidden'; });
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function(es){
      es.forEach(function(en){
        if (!en.isIntersecting) return;
        io.unobserve(en.target);
        var c = en.target.cloneNode(true);
        c.style.visibility = 'visible';
        en.target.parentNode.replaceChild(c, en.target);
      });
    }, { threshold:0.35 });
    Array.prototype.forEach.call(figs, function(el){ io.observe(el); });
  } else {
    Array.prototype.forEach.call(figs, function(el){ el.style.visibility = 'visible'; });
  }
})();
</script>'''

FORM_JS = '''<script>
(function(){
  var f = document.getElementById('wform');
  if (!f) return;
  f.addEventListener('submit', function(e){
    e.preventDefault();
    if (f.checkValidity()) location.href = 'thanks.html';
    else f.reportValidity();
  });
})();
</script>'''

DESC = '15年で築いた18,000社の決裁者ネットワークから、ニーズを確認できた企業だけをお繋ぎします。粗利600万円は上限ではなく、最低保証の下限です。'

# .git は残したまま中身だけ入れ替える
if os.path.isdir(SITE):
    for _e in os.listdir(SITE):
        if _e == ".git": continue
        _p = os.path.join(SITE, _e)
        shutil.rmtree(_p) if os.path.isdir(_p) else os.remove(_p)
os.makedirs(os.path.join(SITE, "assets"), exist_ok=True)
for n in ("logo-w-gold.png","logo-w-watermark.png","logo-w-white.png","logo-w-red.png","emblem-600.png","emblem-800.png","emblem-18000.png","emblem-600-white.png","emblem-800-white.png","exec-taguchi.jpg"):
    shutil.copy(os.path.join(BASE,"assets",n), os.path.join(SITE,"assets",n))
# 人物写真
os.makedirs(os.path.join(SITE, "assets", "person"), exist_ok=True)
for n in sorted(os.listdir(os.path.join(BASE, "assets", "person"))):
    if n.lower().endswith((".jpg", ".png")):
        shutil.copy(os.path.join(BASE,"assets","person",n), os.path.join(SITE,"assets","person",n))

# STEP の写真
os.makedirs(os.path.join(SITE, "assets", "step"), exist_ok=True)
for n in sorted(os.listdir(os.path.join(BASE, "assets", "step"))):
    if n.lower().endswith((".jpg", ".png")):
        shutil.copy(os.path.join(BASE,"assets","step",n), os.path.join(SITE,"assets","step",n))

# 透過イラスト（実際にページから参照されているものだけ）
used = sorted(set(re.findall(r'assets/illust/([\w.-]+\.png)', lp + fm + tk)))
if used:
    os.makedirs(os.path.join(SITE, "assets", "illust"), exist_ok=True)
    for n in used:
        shutil.copy(os.path.join(BASE,"assets","illust",n), os.path.join(SITE,"assets","illust",n))

io.open(os.path.join(SITE,"index.html"),"w",encoding="utf-8").write(
    shell("18,000社から決裁者をご紹介｜W", DESC, lp, LP_JS))
io.open(os.path.join(SITE,"form.html"),"w",encoding="utf-8").write(
    shell("無料で資料をダウンロード｜W", "30秒で完了。サービス内容・審査基準・保証の適用条件をまとめた資料をお送りします。", fm, FORM_JS))
io.open(os.path.join(SITE,"thanks.html"),"w",encoding="utf-8").write(
    shell("資料をお送りしました｜W", "1営業日以内に担当よりご連絡いたします。", tk))
io.open(os.path.join(SITE,".nojekyll"),"w",encoding="utf-8").write("")

for r,d,fs in os.walk(SITE):
    for x in sorted(fs): print(os.path.relpath(os.path.join(r,x), SITE), os.path.getsize(os.path.join(r,x)))
