<script setup lang="ts">
import AuthDemo from './AuthDemo.vue'
</script>
<template>
  <main id="main" class="rdp-page">
    <section class="rdp-hero shell">
      <div class="rdp-hero-copy">
        <p class="rdp-eyebrow">PERSONAL REMOTE ACCESS / OPEN SOURCE</p>
        <h1>远程桌面<br />先认证，<span>再连接。</span></h1>
        <p class="rdp-lead">
          为你的 SakuraFrp 远程桌面，多守一道门。<br />在浏览器中完成认证，再用熟悉的 RDP
          客户端，回到自己的电脑。
        </p>
        <div class="rdp-actions">
          <a class="rdp-button primary" href="/projects/rdp-access-auth/wiki#deployment"
            >开始部署 <span>→</span></a
          ><a class="rdp-button" href="/projects/rdp-access-auth/wiki">阅读 Wiki ↗</a>
        </div>
        <p class="rdp-caption">Python / Flask / SQLite / WebAuthn</p>
      </div>
      <AuthDemo class="rdp-hero-demo" />
    </section>
    <section class="rdp-section shell rdp-reveal" id="features">
      <p class="rdp-eyebrow">01 / AUTHENTICATION</p>
      <h2>选择顺手的认证方式</h2>
      <div class="rdp-grid">
        <article class="rdp-card rdp-reveal">
          <span class="rdp-card-icon">01 / PASSWORD</span>
          <h3>固定访问密码</h3>
          <p>至少 16 位的复杂密码，可重复使用。适合作为首次登录与备用认证方式。</p>
        </article>
        <article class="rdp-card rdp-reveal">
          <span class="rdp-card-icon">02 / TEMPORARY</span>
          <h3>三个词，临时通行</h3>
          <p>来自 Minecraft、原神与美食的随机中文词。成功使用后自动轮换，并显示下一条。</p>
        </article>
        <article class="rdp-card rdp-reveal">
          <span class="rdp-card-icon">03 / PASSKEY</span>
          <h3>通行密钥</h3>
          <p>通过指纹、面容、PIN 或安全密钥确认身份。支持多个密钥，也支持手机跨设备确认。</p>
        </article>
      </div>
    </section>
    <section class="rdp-section shell rdp-split rdp-reveal">
      <div>
        <p class="rdp-eyebrow">02 / HOW IT WORKS</p>
        <h2>把入口留给<br />完成认证的人。</h2>
        <p class="rdp-lead">未经授权的公网 IP，在进入 RDP 登录环节前被拦截。</p>
        <a class="rdp-text-link" href="/projects/rdp-access-auth/wiki#architecture"
          >了解架构与适用范围 →</a
        >
      </div>
      <div class="rdp-facts">
        <article>
          <b>限流与封禁</b>
          <p>
            同一 IP 连续失败 5 次，封禁 15 分钟；10 分钟内 5 个不同 IP 被封禁，全站锁定 15 分钟。
          </p>
        </article>
        <article>
          <b>可选人机验证</b>
          <p>可接入 Cloudflare Turnstile，三种认证方式均由服务端校验。</p>
        </article>
        <article>
          <b>清楚的使用边界</b>
          <p>
            按公网 IP 放行，共享出口的设备共享准入。6
            小时后新连接需重新认证，已建立的会话不保证断开。它不替代系统登录，也不隐藏公网端口。
          </p>
        </article>
      </div>
    </section>
    <section class="rdp-section shell rdp-reveal">
      <div class="rdp-deploy-card">
        <div>
          <p class="rdp-eyebrow">03 / SELF-HOSTED</p>
          <h2>从安装包开始，部署到自己的主机。</h2>
          <p>
            下载匹配的 RPM 或 DEB，再用浏览器向导或终端向导完成配置。<br />Wiki
            提供安装、校验、Cloudflare / SakuraFrp 配置与常见问题排查。
          </p>
        </div>
        <a class="rdp-button primary" href="/projects/rdp-access-auth/wiki#deployment"
          >跟着步骤部署 →</a
        >
      </div>
    </section>
  </main>
</template>
