#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import tempfile
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import requests

try:
  from tailor_resume_for_jd import (
    _clean,
    _generate_with_openai,
    _html_to_text,
    _normalize_payload,
    _write_html_with_preserved_layout,
  )
except ModuleNotFoundError:
  from scripts.tailor_resume_for_jd import (
    _clean,
    _generate_with_openai,
    _html_to_text,
    _normalize_payload,
    _write_html_with_preserved_layout,
  )

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "reports" / "resume_tailoring"

INDEX_HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Resume Tailor Studio</title>
  <style>
    :root {
      --bg: #f5efe4;
      --panel: #fffdfa;
      --panel-strong: #fff8f1;
      --ink: #1d2f38;
      --muted: #5a6b74;
      --line: rgba(29, 47, 56, 0.2);
      --accent: #0f6a63;
      --accent-2: #a4492e;
      --accent-3: #223e63;
      --radius: 16px;
      --shadow: 0 14px 34px rgba(21, 35, 44, 0.14);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      font-family: "Source Han Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 12% 8%, rgba(15, 106, 99, 0.18), transparent 44%),
        radial-gradient(circle at 88% 14%, rgba(164, 73, 46, 0.16), transparent 38%),
        linear-gradient(150deg, #f8f3ea, var(--bg));
      min-height: 100vh;
      padding: 20px 14px 40px;
    }

    .wrap {
      max-width: 1120px;
      margin: 0 auto;
      display: grid;
      gap: 14px;
    }

    .hero {
      border-radius: 24px;
      padding: 24px;
      color: #ecf5f3;
      background: linear-gradient(130deg, #114f4c 0%, #253a58 54%, #3b3148 100%);
      box-shadow: 0 18px 40px rgba(14, 33, 47, 0.24);
      display: grid;
      grid-template-columns: 1.25fr 0.95fr;
      gap: 18px;
    }

    .hero h1 { margin: 0; font-size: clamp(28px, 4vw, 46px); line-height: 1.05; }
    .hero p { margin: 10px 0 0; line-height: 1.65; color: rgba(236, 245, 243, 0.95); }

    .eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 6px 12px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.1);
      border: 1px solid rgba(255, 255, 255, 0.16);
      font-size: 12px;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }

    .hero-copy {
      display: grid;
      gap: 10px;
    }

    .hero-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }

    .hero-lead {
      max-width: 640px;
      font-size: 16px;
    }

    .hero-points {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 4px;
    }

    .hero-points span {
      padding: 7px 12px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.12);
      border: 1px solid rgba(255, 255, 255, 0.16);
      font-size: 13px;
    }

    .lang-switch {
      display: inline-flex;
      gap: 6px;
      padding: 4px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.1);
      border: 1px solid rgba(255, 255, 255, 0.16);
    }

    .lang-btn {
      border: 0;
      border-radius: 999px;
      padding: 7px 12px;
      font-size: 12px;
      line-height: 1;
      color: rgba(236, 245, 243, 0.92);
      background: transparent;
      box-shadow: none;
    }

    .lang-btn.active {
      background: rgba(255, 255, 255, 0.18);
      color: #ffffff;
    }

    .hero-side {
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.16);
      border-radius: 18px;
      padding: 16px;
      display: grid;
      gap: 12px;
      align-content: start;
    }

    .hero-side h2 {
      margin: 0;
      font-size: 18px;
    }

    .hero-side ol {
      margin: 0;
      padding-left: 18px;
      display: grid;
      gap: 10px;
      line-height: 1.55;
      color: rgba(236, 245, 243, 0.96);
    }

    .panel {
      background: rgba(255, 253, 250, 0.9);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: 16px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(2px);
    }

    .panel h2 {
      margin: 0 0 8px;
      font-size: 22px;
    }

    .panel-intro {
      margin: 0 0 14px;
      color: var(--muted);
      line-height: 1.6;
    }

    .info-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }

    .info-card {
      background: var(--panel-strong);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 14px;
    }

    .info-card strong {
      display: block;
      margin-bottom: 6px;
      color: var(--accent-3);
      font-size: 15px;
    }

    .info-card p {
      margin: 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.55;
    }

    .grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }

    .field {
      display: grid;
      gap: 6px;
      margin-bottom: 10px;
    }

    label {
      font-size: 13px;
      color: var(--muted);
    }

    input[type="text"],
    textarea,
    select {
      width: 100%;
      border: 1px solid rgba(29, 47, 56, 0.25);
      border-radius: 10px;
      padding: 10px 12px;
      font-size: 14px;
      background: #fff;
      color: var(--ink);
      outline: none;
    }

    textarea {
      min-height: 180px;
      resize: vertical;
      line-height: 1.5;
    }

    input[type="file"] {
      width: 100%;
      border: 1px dashed rgba(29, 47, 56, 0.35);
      border-radius: 10px;
      padding: 10px;
      background: #fff;
    }

    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 8px;
    }

    button {
      border: 0;
      border-radius: 999px;
      background: linear-gradient(135deg, var(--accent), #135f5a);
      color: #edf7f6;
      padding: 10px 18px;
      font-size: 14px;
      cursor: pointer;
      transition: transform 160ms ease, box-shadow 160ms ease;
      box-shadow: 0 8px 18px rgba(15, 106, 99, 0.28);
    }

    button:hover {
      transform: translateY(-1px);
    }

    button.secondary {
      background: linear-gradient(135deg, var(--accent-2), #8d3f2a);
      box-shadow: 0 8px 18px rgba(164, 73, 46, 0.24);
    }

    .hint {
      font-size: 12px;
      color: var(--muted);
      line-height: 1.45;
    }

    .tips {
      margin-top: 10px;
      padding: 12px 14px;
      border-radius: 12px;
      background: rgba(15, 106, 99, 0.06);
      border: 1px solid rgba(15, 106, 99, 0.12);
      color: #36515b;
      font-size: 13px;
      line-height: 1.55;
    }

    .result {
      display: none;
      margin-top: 6px;
      border-radius: 12px;
      border: 1px solid var(--line);
      background: #fff;
      padding: 12px;
    }

    .result.show { display: block; }

    .status {
      font-size: 14px;
      min-height: 20px;
      color: #24444a;
    }

    .error {
      color: #8a2a2a;
    }

    .link-row {
      display: grid;
      gap: 6px;
      margin-top: 8px;
    }

    .link-row a {
      color: #0d5964;
      word-break: break-all;
    }

    .footer-note {
      color: var(--muted);
      font-size: 12px;
      text-align: center;
      padding: 2px 4px 0;
    }

    @media (max-width: 860px) {
      .hero { grid-template-columns: 1fr; }
      .info-grid { grid-template-columns: 1fr; }
      .grid { grid-template-columns: 1fr; }
      textarea { min-height: 150px; }
    }
  </style>
</head>
<body>
  <main class="wrap">
    <section class="hero">
      <div class="hero-copy">
        <div class="hero-top">
          <div class="eyebrow" id="eyebrowText">Resume Tailor Studio</div>
          <div class="lang-switch" aria-label="Language switcher">
            <button id="langZhBtn" class="lang-btn active" type="button">中文</button>
            <button id="langEnBtn" class="lang-btn" type="button">EN</button>
          </div>
        </div>
        <h1 id="heroTitle">把一份已有简历，快速改成更贴近目标 JD 的版本</h1>
        <p id="heroLead" class="hero-lead">输入现有简历 HTML 链接，再贴入新的岗位描述，系统会分析 JD 重点、保留原页面结构，并生成一份更适配岗位方向的新简历页面。</p>
        <div class="hero-points">
          <span id="heroPoint1">保留原版式</span>
          <span id="heroPoint2">支持 JD 文本 / 图片</span>
          <span id="heroPoint3">输出新 HTML 页面</span>
          <span id="heroPoint4">可切换 conservative / balanced / aggressive</span>
        </div>
      </div>
      <aside class="hero-side">
        <h2 id="stepsTitle">三步完成</h2>
        <ol>
          <li id="step1">提供现有简历 HTML 链接，作为原始模板。</li>
          <li id="step2">粘贴目标 JD，或上传岗位截图做 OCR 提取。</li>
          <li id="step3">选择改写力度，生成新的适配简历页面并直接打开预览。</li>
        </ol>
      </aside>
    </section>

    <section class="panel">
      <h2 id="scenarioTitle">它适合什么场景</h2>
      <p id="scenarioIntro" class="panel-intro">如果你已经有一版网页简历，不想重做视觉样式，只想围绕某个岗位快速改写内容、提炼匹配重点，这个工具就是为这个流程准备的。</p>
      <div class="info-grid">
        <article class="info-card">
          <strong id="card1Title">保留版式</strong>
          <p id="card1Body">不推倒重来，优先沿用你已有的 HTML 结构和视觉表达，减少重复排版成本。</p>
        </article>
        <article class="info-card">
          <strong id="card2Title">突出匹配</strong>
          <p id="card2Body">围绕 JD 里的职责、关键词和能力要求，输出更聚焦的经历措辞和摘要说明。</p>
        </article>
        <article class="info-card">
          <strong id="card3Title">先试再精修</strong>
          <p id="card3Body">适合先生成一个可讨论版本，再继续手工优化成最终投递稿。</p>
        </article>
      </div>
    </section>

    <section class="panel">
      <h2 id="formTitle">开始生成</h2>
      <p id="formIntro" class="panel-intro">建议先用一份已经整理好的 HTML 简历作为输入。若当前未配置大模型 key，系统会使用本地规则模式生成结果。</p>
      <div class="grid">
        <div>
          <div class="field">
            <label id="resumeHtmlLabel" for="resumeHtmlUrl">简历 HTML 链接或本地路径</label>
            <input id="resumeHtmlUrl" type="text" placeholder="例如: file:///C:/.../vickie_resume_profile.html 或 https://..." />
          </div>

          <div class="field">
            <label id="jobTitleLabel" for="jobTitle">目标岗位（可选）</label>
            <input id="jobTitle" type="text" placeholder="例如: AI Agent 产品经理" />
          </div>

          <div class="field">
            <label id="outputLanguageLabel" for="language">输出语言</label>
            <select id="language">
              <option id="outputLanguageOptionZh" value="zh" selected>中文</option>
              <option id="outputLanguageOptionEn" value="en">English</option>
              <option id="outputLanguageOptionBi" value="bilingual">中英双语</option>
            </select>
          </div>

          <div class="field">
            <label id="rewriteStrengthLabel" for="version">改写力度</label>
            <select id="version">
              <option value="conservative">conservative</option>
              <option value="balanced">balanced</option>
              <option value="aggressive" selected>aggressive</option>
            </select>
          </div>
        </div>

        <div>
          <div class="field">
            <label id="jdTextLabel" for="jdText">JD 文本（优先）</label>
            <textarea id="jdText" placeholder="直接粘贴岗位职责、要求、关键词等内容"></textarea>
          </div>

          <div class="field">
            <label id="jdImageLabel" for="jdImage">JD 图片（可选，文本为空时使用 OCR）</label>
            <input id="jdImage" type="file" accept="image/*" />
          </div>

          <p id="ocrHint" class="hint">说明：如果只上传图片，后端会尝试基于 OPENAI_API_KEY 进行图片文字提取。未配置时会提示失败原因。</p>
          <div id="tipsBox" class="tips">
            <strong id="tipsTitle">建议输入方式：</strong><br />
            <span id="tipsLine1">1. 优先粘贴完整 JD 文本，结果最稳定。</span><br />
            <span id="tipsLine2">2. 如果你只想快速试跑，可以先点“填充当前编辑页示例”。</span><br />
            <span id="tipsLine3">3. 如果生成结果偏保守，通常说明当前运行在无 key 的规则模式。</span>
          </div>
        </div>
      </div>

      <div class="actions">
        <button id="generateBtn" type="button">生成适配简历页面</button>
        <button id="fillDemoBtn" class="secondary" type="button">填充当前编辑页示例</button>
      </div>

      <p id="status" class="status"></p>

      <section id="resultBox" class="result">
        <strong id="resultTitle">生成结果</strong>
        <div class="link-row" id="resultLinks"></div>
      </section>
    </section>

    <p id="footerNote" class="footer-note">生成结果会写入服务端本地输出目录，并返回新页面链接与摘要 JSON，便于继续迭代。</p>
  </main>

  <script>
    const generateBtn = document.getElementById("generateBtn");
    const fillDemoBtn = document.getElementById("fillDemoBtn");
    const langZhBtn = document.getElementById("langZhBtn");
    const langEnBtn = document.getElementById("langEnBtn");
    const statusEl = document.getElementById("status");
    const resultBox = document.getElementById("resultBox");
    const resultLinks = document.getElementById("resultLinks");
    let currentUiLang = "zh";

    const translations = {
      zh: {
        eyebrowText: "Resume Tailor Studio",
        heroTitle: "把一份已有简历，快速改成更贴近目标 JD 的版本",
        heroLead: "输入现有简历 HTML 链接，再贴入新的岗位描述，系统会分析 JD 重点、保留原页面结构，并生成一份更适配岗位方向的新简历页面。",
        heroPoint1: "保留原版式",
        heroPoint2: "支持 JD 文本 / 图片",
        heroPoint3: "输出新 HTML 页面",
        heroPoint4: "可切换 conservative / balanced / aggressive",
        stepsTitle: "三步完成",
        step1: "提供现有简历 HTML 链接，作为原始模板。",
        step2: "粘贴目标 JD，或上传岗位截图做 OCR 提取。",
        step3: "选择改写力度，生成新的适配简历页面并直接打开预览。",
        scenarioTitle: "它适合什么场景",
        scenarioIntro: "如果你已经有一版网页简历，不想重做视觉样式，只想围绕某个岗位快速改写内容、提炼匹配重点，这个工具就是为这个流程准备的。",
        card1Title: "保留版式",
        card1Body: "不推倒重来，优先沿用你已有的 HTML 结构和视觉表达，减少重复排版成本。",
        card2Title: "突出匹配",
        card2Body: "围绕 JD 里的职责、关键词和能力要求，输出更聚焦的经历措辞和摘要说明。",
        card3Title: "先试再精修",
        card3Body: "适合先生成一个可讨论版本，再继续手工优化成最终投递稿。",
        formTitle: "开始生成",
        formIntro: "建议先用一份已经整理好的 HTML 简历作为输入。若当前未配置大模型 key，系统会使用本地规则模式生成结果。",
        resumeHtmlLabel: "简历 HTML 链接或本地路径",
        resumeHtmlPlaceholder: "例如: file:///C:/.../vickie_resume_profile.html 或 https://...",
        jobTitleLabel: "目标岗位（可选）",
        jobTitlePlaceholder: "例如: AI Agent 产品经理",
        outputLanguageLabel: "输出语言",
        outputLanguageOptionZh: "中文",
        outputLanguageOptionEn: "English",
        outputLanguageOptionBi: "中英双语",
        rewriteStrengthLabel: "改写力度",
        jdTextLabel: "JD 文本（优先）",
        jdTextPlaceholder: "直接粘贴岗位职责、要求、关键词等内容",
        jdImageLabel: "JD 图片（可选，文本为空时使用 OCR）",
        ocrHint: "说明：如果只上传图片，后端会尝试基于 OPENAI_API_KEY 进行图片文字提取。未配置时会提示失败原因。",
        tipsTitle: "建议输入方式：",
        tipsLine1: "1. 优先粘贴完整 JD 文本，结果最稳定。",
        tipsLine2: "2. 如果你只想快速试跑，可以先点“填充当前编辑页示例”。",
        tipsLine3: "3. 如果生成结果偏保守，通常说明当前运行在无 key 的规则模式。",
        generateBtn: "生成适配简历页面",
        fillDemoBtn: "填充当前编辑页示例",
        resultTitle: "生成结果",
        footerNote: "生成结果会写入服务端本地输出目录，并返回新页面链接与摘要 JSON，便于继续迭代。",
        statusGenerating: "正在生成，请稍候...",
        statusDone: "生成完成。你可以直接打开新页面预览。",
        statusFillDemo: "示例已填充，可直接点击生成。",
        fileUrlLabel: "本地文件 URL",
        absPathLabel: "文件路径",
        relPathLabel: "相对路径",
        summaryJsonLabel: "摘要 JSON",
        readImageError: "读取图片失败",
        genericError: "生成失败",
      },
      en: {
        eyebrowText: "Resume Tailor Studio",
        heroTitle: "Turn an existing resume into a version that matches a target JD faster",
        heroLead: "Provide an existing resume HTML link and paste a new job description. The system will analyze the JD, preserve your original layout, and generate a more targeted resume page.",
        heroPoint1: "Keep original layout",
        heroPoint2: "Supports JD text / image",
        heroPoint3: "Outputs a new HTML page",
        heroPoint4: "Switch between conservative / balanced / aggressive",
        stepsTitle: "Complete in 3 steps",
        step1: "Provide an existing resume HTML link as the source template.",
        step2: "Paste the target JD or upload a job screenshot for OCR extraction.",
        step3: "Choose rewrite intensity and generate a tailored resume page ready for preview.",
        scenarioTitle: "When this is useful",
        scenarioIntro: "If you already have a web-based resume and do not want to redesign the visual layer, this tool helps you quickly rewrite the content around a specific role and surface stronger matching signals.",
        card1Title: "Preserve layout",
        card1Body: "Reuse your existing HTML structure and visual design instead of rebuilding the resume from scratch.",
        card2Title: "Highlight fit",
        card2Body: "Rewrite experience around responsibilities, keywords, and capability signals found in the JD.",
        card3Title: "Draft first, refine later",
        card3Body: "Generate a discussion-ready version first, then continue polishing it into a final application draft.",
        formTitle: "Start generating",
        formIntro: "It is best to begin with a clean HTML resume as the input template. If no model key is configured, the app will fall back to local rule-based generation.",
        resumeHtmlLabel: "Resume HTML link or local path",
        resumeHtmlPlaceholder: "For example: file:///C:/.../vickie_resume_profile.html or https://...",
        jobTitleLabel: "Target role (optional)",
        jobTitlePlaceholder: "For example: AI Agent Product Manager",
        outputLanguageLabel: "Output language",
        outputLanguageOptionZh: "Chinese",
        outputLanguageOptionEn: "English",
        outputLanguageOptionBi: "Bilingual",
        rewriteStrengthLabel: "Rewrite intensity",
        jdTextLabel: "JD text (preferred)",
        jdTextPlaceholder: "Paste responsibilities, requirements, and keywords here",
        jdImageLabel: "JD image (optional, OCR is used when text is empty)",
        ocrHint: "Note: if you upload an image only, the backend will try OCR with OPENAI_API_KEY. If the key is missing, the app will show the failure reason.",
        tipsTitle: "Recommended input flow:",
        tipsLine1: "1. Paste the full JD text first for the most stable result.",
        tipsLine2: "2. If you only want a quick trial, click the demo-fill button first.",
        tipsLine3: "3. If the result feels conservative, the app is likely running in no-key fallback mode.",
        generateBtn: "Generate tailored resume page",
        fillDemoBtn: "Fill current demo example",
        resultTitle: "Generated output",
        footerNote: "Generated output is written to the server-side output folder and returned as a new page link plus summary JSON for further iteration.",
        statusGenerating: "Generating, please wait...",
        statusDone: "Done. You can open the new page to preview it.",
        statusFillDemo: "Demo content inserted. You can generate immediately.",
        fileUrlLabel: "Local file URL",
        absPathLabel: "Absolute path",
        relPathLabel: "Relative path",
        summaryJsonLabel: "Summary JSON",
        readImageError: "Failed to read image file",
        genericError: "Generation failed",
      }
    };

    function t(key) {
      return translations[currentUiLang][key] || key;
    }

    function applyLanguage(lang) {
      currentUiLang = lang;
      document.documentElement.lang = lang === "en" ? "en" : "zh-CN";
      langZhBtn.classList.toggle("active", lang === "zh");
      langEnBtn.classList.toggle("active", lang === "en");

      const textIds = [
        "eyebrowText", "heroTitle", "heroLead", "heroPoint1", "heroPoint2", "heroPoint3", "heroPoint4",
        "stepsTitle", "step1", "step2", "step3", "scenarioTitle", "scenarioIntro", "card1Title", "card1Body",
        "card2Title", "card2Body", "card3Title", "card3Body", "formTitle", "formIntro", "resumeHtmlLabel",
        "jobTitleLabel", "outputLanguageLabel", "outputLanguageOptionZh", "outputLanguageOptionEn", "outputLanguageOptionBi",
        "rewriteStrengthLabel", "jdTextLabel", "jdImageLabel", "ocrHint", "tipsTitle", "tipsLine1", "tipsLine2",
        "tipsLine3", "generateBtn", "fillDemoBtn", "resultTitle", "footerNote"
      ];

      for (const id of textIds) {
        const node = document.getElementById(id);
        if (node) node.textContent = t(id);
      }

      document.getElementById("resumeHtmlUrl").placeholder = t("resumeHtmlPlaceholder");
      document.getElementById("jobTitle").placeholder = t("jobTitlePlaceholder");
      document.getElementById("jdText").placeholder = t("jdTextPlaceholder");
    }

    function setStatus(text, isError = false) {
      statusEl.textContent = text || "";
      statusEl.classList.toggle("error", Boolean(isError));
    }

    function clearResult() {
      resultLinks.innerHTML = "";
      resultBox.classList.remove("show");
    }

    async function fileToDataUrl(file) {
      if (!file) return "";
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result || "");
        reader.onerror = () => reject(new Error(t("readImageError")));
        reader.readAsDataURL(file);
      });
    }

    function renderLinks(data) {
      const lines = [];
      if (data.output_html_file_url) {
        lines.push([t("fileUrlLabel"), data.output_html_file_url]);
      }
      if (data.output_html_abs_path) {
        lines.push([t("absPathLabel"), data.output_html_abs_path]);
      }
      if (data.output_html_rel_path) {
        lines.push([t("relPathLabel"), data.output_html_rel_path]);
      }
      if (data.summary_json_path) {
        lines.push([t("summaryJsonLabel"), data.summary_json_path]);
      }

      for (const pair of lines) {
        const row = document.createElement("div");
        const label = document.createElement("span");
        label.textContent = pair[0] + ": ";
        const link = document.createElement("a");
        link.href = pair[1];
        link.textContent = pair[1];
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        row.appendChild(label);
        row.appendChild(link);
        resultLinks.appendChild(row);
      }

      resultBox.classList.add("show");
    }

    generateBtn.addEventListener("click", async () => {
      clearResult();
      setStatus(t("statusGenerating"));

      try {
        const jdImageFile = document.getElementById("jdImage").files[0];
        const jdImageDataUrl = await fileToDataUrl(jdImageFile);

        const body = {
          resume_html_url: document.getElementById("resumeHtmlUrl").value.trim(),
          jd_text: document.getElementById("jdText").value.trim(),
          jd_image_data_url: jdImageDataUrl,
          job_title: document.getElementById("jobTitle").value.trim(),
          language: document.getElementById("language").value,
          version: document.getElementById("version").value,
        };

        const res = await fetch("/api/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });

        const data = await res.json();
        if (!res.ok || !data.ok) {
          throw new Error(data.error || t("genericError"));
        }

        setStatus(t("statusDone"), false);
        renderLinks(data);
      } catch (err) {
        setStatus(err.message || t("genericError"), true);
      }
    });

    fillDemoBtn.addEventListener("click", () => {
      document.getElementById("resumeHtmlUrl").value = "reports/resume_tailoring/2026-06-23_html_preserve/vickie_resume_profile_jd_tailored.html";
      document.getElementById("jobTitle").value = "AI Agent 产品经理";
      document.getElementById("language").value = "zh";
      document.getElementById("version").value = "aggressive";
      if (!document.getElementById("jdText").value.trim()) {
        document.getElementById("jdText").value = "负责 AI Agent 产品从需求定义到上线迭代的全流程，联动研发与业务团队，推动多场景落地并对结果指标负责。";
      }
      setStatus(t("statusFillDemo"), false);
    });

    langZhBtn.addEventListener("click", () => applyLanguage("zh"));
    langEnBtn.addEventListener("click", () => applyLanguage("en"));

    applyLanguage("zh");
  </script>
</body>
</html>
"""


def _json_response(handler: BaseHTTPRequestHandler, status: int, body: dict[str, Any]) -> None:
    content = json.dumps(body, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(content)))
    handler.end_headers()
    handler.wfile.write(content)


def _read_json_body(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    size = int(handler.headers.get("Content-Length", "0") or "0")
    raw = handler.rfile.read(size) if size > 0 else b""
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


def _resolve_resume_html_source(source: str) -> tuple[str, str]:
    src = _clean(source)
    if not src:
        raise ValueError("resume_html_url 不能为空")

    if re.match(r"^https?://", src, flags=re.IGNORECASE):
        resp = requests.get(src, timeout=30)
        resp.raise_for_status()
        ctype = resp.headers.get("Content-Type", "")
        if "text/html" not in ctype and "application/xhtml+xml" not in ctype:
            # Still allow if body appears html-like.
            if "<html" not in resp.text.lower():
                raise ValueError("提供的链接未返回 HTML 内容")
        return resp.text, src

    if src.lower().startswith("file://"):
        parsed = urlparse(src)
        file_path = unquote(parsed.path or "")
        if re.match(r"^/[A-Za-z]:", file_path):
            file_path = file_path[1:]
        path = Path(file_path)
    else:
        path = Path(src)
        if not path.is_absolute():
            path = (ROOT / path).resolve()

    if not path.exists():
        raise ValueError(f"HTML 文件不存在: {path}")

    text = path.read_text(encoding="utf-8")
    return text, path.as_uri()


def _extract_jd_text_from_image(data_url: str) -> str:
    data = _clean(data_url)
    if not data:
        return ""

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("未检测到 OPENAI_API_KEY，无法对 JD 图片做文字提取")

    if not data.lower().startswith("data:image/"):
        raise ValueError("JD 图片格式无效，需为 data URL")

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    endpoint = f"{base_url}/chat/completions"
    model = os.getenv("RESUME_JD_OCR_MODEL", "gpt-4.1-mini")

    payload = {
        "model": model,
        "temperature": 0,
        "messages": [
            {
                "role": "system",
                "content": "You extract job description text from an image. Output plain text only.",
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract all readable JD content from this image and return plain text."},
                    {"type": "image_url", "image_url": {"url": data}},
                ],
            },
        ],
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(endpoint, headers=headers, data=json.dumps(payload, ensure_ascii=False), timeout=120)
        response.raise_for_status()
        body = response.json()
        text = _clean(body.get("choices", [{}])[0].get("message", {}).get("content"))
        if not text:
            raise ValueError("图片文字提取结果为空")
        return text
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"JD 图片文字提取失败: {exc}") from exc


def _safe_name(value: str, fallback: str = "job") -> str:
    text = _clean(value) or fallback
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"[^A-Za-z0-9_\-\u4e00-\u9fff]", "", text)
    text = text[:48]
    return text or fallback


def _build_summary_block(payload: dict[str, Any], job_title: str, version: str, jd_text: str, source_label: str) -> str:
    focus_items = payload.get("jd_focus", [])[:8]
    gap_items = payload.get("gaps", [])[:4]
    keyword_items = payload.get("versions", {}).get(version, {}).get("keyword_coverage", [])[:10]

    focus_html = "".join(f"<li>{_clean(item)}</li>" for item in focus_items if _clean(item))
    gap_html = "".join(f"<li>{_clean(item)}</li>" for item in gap_items if _clean(item))
    keyword_html = "".join(f"<span>{_clean(item)}</span>" for item in keyword_items if _clean(item))

    jd_excerpt = _clean(jd_text)
    if len(jd_excerpt) > 420:
        jd_excerpt = jd_excerpt[:420].rstrip() + "..."

    return f"""
    <section style="margin: 0 0 16px; padding: 18px 20px; border-radius: 20px; background: linear-gradient(135deg, rgba(15, 106, 99, 0.1), rgba(164, 73, 46, 0.08)); border: 1px solid rgba(29, 47, 56, 0.16); box-shadow: 0 10px 24px rgba(27, 36, 48, 0.08);">
      <div style="display:grid; gap:14px; grid-template-columns: 1.25fr 1fr; align-items:start;">
        <div>
          <div style="display:flex; flex-wrap:wrap; gap:8px; margin-bottom:10px;">
            <span style="padding:4px 10px; border-radius:999px; background:rgba(15, 106, 99, 0.14); color:#0f5f59; font-size:12px;">JD 适配摘要</span>
            <span style="padding:4px 10px; border-radius:999px; background:rgba(178, 82, 44, 0.12); color:#9d4625; font-size:12px;">{_clean(version)}</span>
            <span style="padding:4px 10px; border-radius:999px; background:rgba(29, 47, 56, 0.08); color:#40505a; font-size:12px;">{_clean(job_title) or 'N/A'}</span>
          </div>
          <h2 style="margin:0 0 8px; font-size:24px; color:#16343f;">这份简历是按这个 JD 重新对齐的</h2>
          <p style="margin:0; line-height:1.65; color:#344650;">来源: {_clean(source_label)}。当前版本保留原简历骨架，但会围绕 JD 关键词重写经历要点，并把适配重点前置到页面顶部。</p>
          <div style="margin-top:12px; line-height:1.65; color:#344650;">
            <strong>JD 摘要：</strong>{jd_excerpt}
          </div>
        </div>
        <div>
          <h3 style="margin:0 0 8px; font-size:16px; color:#16343f;">重点匹配</h3>
          <ul style="margin:0; padding-left:18px; display:grid; gap:6px; line-height:1.55; color:#33444f;">{focus_html}</ul>
          <h3 style="margin:14px 0 8px; font-size:16px; color:#16343f;">可补强点</h3>
          <ul style="margin:0; padding-left:18px; display:grid; gap:6px; line-height:1.55; color:#33444f;">{gap_html}</ul>
          <div style="display:flex; flex-wrap:wrap; gap:8px; margin-top:12px;">
            {keyword_html}
          </div>
        </div>
      </div>
    </section>
    """


def _inject_summary_block(html_text: str, summary_block: str) -> str:
    body_match = re.search(r"<body[^>]*>", html_text, flags=re.IGNORECASE)
    if not body_match:
        return summary_block + html_text

    insert_at = body_match.end()
    return html_text[:insert_at] + "\n  " + summary_block.strip() + "\n" + html_text[insert_at:]


def _run_tailor(
    resume_html_url: str,
    jd_text: str,
    jd_image_data_url: str,
    job_title: str,
    language: str,
    version: str,
) -> dict[str, Any]:
    html_text, source_label = _resolve_resume_html_source(resume_html_url)

    final_jd_text = _clean(jd_text)
    if not final_jd_text and _clean(jd_image_data_url):
        final_jd_text = _extract_jd_text_from_image(jd_image_data_url)

    if not final_jd_text:
        raise ValueError("请提供 JD 文本，或上传可识别的 JD 图片")

    resume_text = _html_to_text(html_text)
    versions = [version] if version in {"conservative", "balanced", "aggressive"} else ["aggressive"]

    raw_payload = _generate_with_openai(
        resume_text=resume_text,
        jd_text=final_jd_text,
        language=language if language in {"zh", "en", "bilingual"} else "zh",
        versions=versions,
        model=os.getenv("RESUME_TAILOR_MODEL", "gpt-4o-mini"),
        job_title=job_title,
    )
    payload = _normalize_payload(raw_payload, versions)

    run_date = dt.date.today().isoformat()
    stamp = dt.datetime.now().strftime("%H%M%S")
    out_dir = OUT_ROOT / (run_date + "_web")
    out_dir.mkdir(parents=True, exist_ok=True)

    safe_job = _safe_name(job_title or "job")
    output_name = f"resume_tailored_{safe_job}_{versions[0]}_{stamp}.html"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as tmp:
      tmp.write(html_text)
      template_path = Path(tmp.name)

    try:
        output_html_path = out_dir / output_name
        ok, message = _write_html_with_preserved_layout(
            template_html_path=template_path,
            output_html_path=output_html_path,
            payload=payload,
            version=versions[0],
        )
        if not ok:
            raise ValueError(message)

        rendered_html = output_html_path.read_text(encoding="utf-8")
        summary_block = _build_summary_block(payload, job_title, versions[0], final_jd_text, source_label)
        rendered_html = _inject_summary_block(rendered_html, summary_block)
        output_html_path.write_text(rendered_html, encoding="utf-8")
    finally:
        try:
            template_path.unlink(missing_ok=True)
        except Exception:
            pass

    summary = {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "source_resume": source_label,
        "job_title": _clean(job_title),
        "language": language,
        "version": versions[0],
        "provider": payload.get("meta", {}).get("provider", "unknown"),
        "jd_focus": payload.get("jd_focus", []),
        "gaps": payload.get("gaps", []),
        "output_html": str(output_html_path),
    }

    summary_path = output_html_path.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "ok": True,
        "output_html_abs_path": str(output_html_path.resolve()),
        "output_html_rel_path": str(output_html_path.relative_to(ROOT)).replace("\\", "/"),
        "output_html_file_url": output_html_path.resolve().as_uri(),
        "summary_json_path": str(summary_path.resolve().as_uri()),
        "provider": payload.get("meta", {}).get("provider", "unknown"),
    }


class ResumeTailorHandler(BaseHTTPRequestHandler):
    server_version = "ResumeTailorHTTP/1.0"

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        # Keep terminal output concise.
        return

    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/", "/index.html"}:
            content = INDEX_HTML.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        _json_response(self, HTTPStatus.NOT_FOUND, {"ok": False, "error": "Not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/generate":
            _json_response(self, HTTPStatus.NOT_FOUND, {"ok": False, "error": "Not found"})
            return

        try:
            data = _read_json_body(self)
            result = _run_tailor(
                resume_html_url=_clean(data.get("resume_html_url")),
                jd_text=_clean(data.get("jd_text")),
                jd_image_data_url=_clean(data.get("jd_image_data_url")),
                job_title=_clean(data.get("job_title")),
                language=_clean(data.get("language")) or "zh",
                version=_clean(data.get("version")) or "aggressive",
            )
            _json_response(self, HTTPStatus.OK, result)
        except Exception as exc:  # noqa: BLE001
            _json_response(self, HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Local web UI for HTML resume tailoring by JD text/image.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=8787, help="Port to bind")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), ResumeTailorHandler)
    print(f"Resume Tailor Studio running at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
