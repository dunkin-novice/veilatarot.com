/* Veila Share System v1 — self-contained.
 *
 * Pure client-side canvas rendering. No backend, no upload.
 *
 * Public API:
 *   window.veilaShare.shareCard(cardOptions)       // 1080×1350 Instagram portrait
 *   window.veilaShare.shareReading(readingOptions) // 1080×1920 Instagram Story
 *
 * Each shareX(...) call: renders a PNG blob in <canvas>, then opens a
 * slide-up share sheet with Download + Native Share + Copy Link.
 *
 * The sheet UI styles itself by injecting one <style data-veila-share>
 * into <head> on first use.
 *
 * Analytics events are fired through window.veilaFire(name, params)
 * (the gtag bridge in /assets/analytics.js).
 */
(function () {
  // ============================================================
  // Style injection — runs once
  // ============================================================
  const CSS = `
.veila-share-sheet {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  pointer-events: none;
  font-family: "Inter", "IBM Plex Sans Thai", -apple-system, BlinkMacSystemFont, sans-serif;
}
.veila-share-sheet .vss-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(10,10,12,0.78);
  -webkit-backdrop-filter: blur(4px);
  backdrop-filter: blur(4px);
  opacity: 0;
  transition: opacity 0.25s ease;
  pointer-events: auto;
}
.veila-share-sheet .vss-body {
  position: relative;
  background: #111218;
  border-top: 1px solid #7a6645;
  border-radius: 4px 4px 0 0;
  width: 100%;
  max-width: 480px;
  max-height: 94vh;
  padding: 18px 18px max(20px, env(safe-area-inset-bottom));
  pointer-events: auto;
  transform: translateY(100%);
  transition: transform 0.3s cubic-bezier(.4,0,.2,1);
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}
.veila-share-sheet.vss-open .vss-backdrop { opacity: 1; }
.veila-share-sheet.vss-open .vss-body { transform: translateY(0); }
.veila-share-sheet.vss-closing .vss-backdrop { opacity: 0; }
.veila-share-sheet.vss-closing .vss-body { transform: translateY(100%); }
.veila-share-sheet .vss-close {
  position: absolute;
  top: 10px;
  right: 14px;
  background: transparent;
  border: 0;
  color: #6c6a63;
  font-size: 30px;
  line-height: 1;
  cursor: pointer;
  padding: 4px 10px;
  transition: color 0.3s ease;
}
.veila-share-sheet .vss-close:hover { color: #b89968; }
.veila-share-sheet .vss-eyebrow {
  font-size: 10px;
  letter-spacing: 0.32em;
  text-transform: uppercase;
  color: #b89968;
  text-align: center;
  margin: 4px 0 16px;
}
.veila-share-sheet .vss-preview {
  margin: 4px 0 14px;
  display: flex;
  justify-content: center;
  min-height: 180px;
  align-items: center;
}
.veila-share-sheet .vss-preview img {
  max-width: 100%;
  /* Mobile-first cap so the three action buttons + hint sit inside the
     94vh sheet without scrolling on a 667-tall phone. The desktop
     media query below lifts this back to 58vh. */
  max-height: 42vh;
  border: 1px solid #7a6645;
  border-radius: 4px;
  box-shadow: 0 12px 40px rgba(0,0,0,0.45);
  display: block;
  /* iOS Safari: long-press on the preview image triggers Save to Photos.
     Allow that gesture by NOT setting -webkit-user-select / callout to none. */
  -webkit-touch-callout: default;
}
.veila-share-sheet .vss-press-hint {
  font-family: "Cormorant Garamond", "IBM Plex Sans Thai", serif;
  font-style: italic;
  color: #b9b3a4;
  font-size: 14px;
  line-height: 1.45;
  text-align: center;
  margin: -10px 4px 16px;
}
.veila-share-sheet .vss-loading {
  font-family: "Cormorant Garamond", "IBM Plex Sans Thai", serif;
  font-style: italic;
  color: #6c6a63;
  font-size: 18px;
}
.veila-share-sheet .vss-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.veila-share-sheet .vss-action {
  background: transparent;
  border: 1px solid #2a2823;
  color: #b9b3a4;
  padding: 14px 24px;
  font-family: inherit;
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.28em;
  text-transform: uppercase;
  cursor: pointer;
  transition: border-color 0.3s ease, color 0.3s ease, background 0.3s ease;
  border-radius: 0;
}
.veila-share-sheet .vss-action:hover {
  border-color: #b89968;
  color: #ebe4d4;
}
.veila-share-sheet .vss-action.vss-action-primary {
  border-color: #b89968;
  color: #ebe4d4;
}
.veila-share-sheet .vss-action.vss-action-primary:hover {
  background: #b89968;
  color: #0a0a0c;
}
@media (min-width: 720px) {
  .veila-share-sheet { align-items: center; }
  .veila-share-sheet .vss-body {
    max-width: 520px;
    max-height: 92vh;
    padding: 24px 22px 28px;
    border-radius: 4px;
    border: 1px solid #7a6645;
    transform: translateY(24px);
  }
  .veila-share-sheet.vss-open .vss-body { transform: translateY(0); }
  .veila-share-sheet .vss-preview { margin: 4px 0 22px; min-height: 240px; }
  .veila-share-sheet .vss-preview img { max-height: 58vh; }
}
`;
  if (!document.querySelector('style[data-veila-share]')) {
    const style = document.createElement('style');
    style.setAttribute('data-veila-share', '1');
    style.textContent = CSS;
    document.head.appendChild(style);
  }

  // ============================================================
  // Analytics bridge
  // ============================================================
  function track(event, params) {
    if (typeof window.veilaFire === 'function') {
      try { window.veilaFire(event, params || {}); } catch (e) {}
    }
  }

  // ============================================================
  // Font readiness — wait for web fonts before canvas text
  // ============================================================
  async function fontsReady() {
    if (document.fonts && document.fonts.ready) {
      try { await document.fonts.ready; } catch (e) {}
    }
  }

  // ============================================================
  // Canvas helpers
  // ============================================================

  // Draw centered text with manual letter-spacing (Canvas has no
  // letter-spacing CSS — emulate per-glyph for the brand wordmark).
  function drawTracked(ctx, text, cx, y, fontSize, trackPx) {
    const chars = Array.from(text);
    const widths = chars.map(c => ctx.measureText(c).width);
    const total = widths.reduce((a, b) => a + b, 0)
      + trackPx * Math.max(0, chars.length - 1);
    let x = cx - total / 2;
    const prevAlign = ctx.textAlign;
    ctx.textAlign = 'left';
    chars.forEach((c, i) => {
      ctx.fillText(c, x, y);
      x += widths[i] + trackPx;
    });
    ctx.textAlign = prevAlign;
  }

  // Word-wrap (space-separated; ASCII/EN). Returns array of lines.
  function wrapEn(ctx, text, maxWidth) {
    const tokens = String(text).split(/(\s+)/);
    const lines = [];
    let cur = '';
    for (const t of tokens) {
      const trial = cur + t;
      if (ctx.measureText(trial).width > maxWidth && cur.trim()) {
        lines.push(cur.trim());
        cur = t.replace(/^\s+/, '');
      } else {
        cur = trial;
      }
    }
    if (cur.trim()) lines.push(cur.trim());
    return lines;
  }

  // Char-wrap (Thai or any unspaced script).
  function wrapTh(ctx, text, maxWidth) {
    const chars = Array.from(String(text));
    const lines = [];
    let cur = '';
    for (const c of chars) {
      const trial = cur + c;
      if (ctx.measureText(trial).width > maxWidth && cur) {
        lines.push(cur);
        cur = c;
      } else {
        cur = trial;
      }
    }
    if (cur) lines.push(cur);
    return lines;
  }

  // Wrap by detecting whether the text contains Thai.
  function wrap(ctx, text, maxWidth) {
    if (/[฀-๿]/.test(text)) return wrapTh(ctx, text, maxWidth);
    return wrapEn(ctx, text, maxWidth);
  }

  function drawWrapped(ctx, text, cx, y, maxWidth, lineHeight, maxLines) {
    let lines = wrap(ctx, text, maxWidth);
    let truncated = false;
    if (lines.length > maxLines) {
      lines = lines.slice(0, maxLines);
      truncated = true;
    }
    lines.forEach((line, i) => {
      let toDraw = line;
      if (truncated && i === lines.length - 1) {
        toDraw = (line.replace(/[.,;:]$/, '')) + '…';
        // Ensure ellipsis fits
        while (ctx.measureText(toDraw).width > maxWidth && toDraw.length > 4) {
          toDraw = toDraw.slice(0, -2) + '…';
        }
      }
      ctx.fillText(toDraw, cx, y + i * lineHeight);
    });
    return { lines: lines.length, height: lines.length * lineHeight };
  }

  // Divider ornament: ── ◇ ──
  function drawDivider(ctx, cx, cy, halfLineWidth, diamondSize) {
    ctx.save();
    ctx.strokeStyle = '#7a6645';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(cx - halfLineWidth, cy);
    ctx.lineTo(cx - diamondSize - 16, cy);
    ctx.moveTo(cx + diamondSize + 16, cy);
    ctx.lineTo(cx + halfLineWidth, cy);
    ctx.stroke();
    ctx.strokeStyle = '#b89968';
    ctx.beginPath();
    ctx.moveTo(cx, cy - diamondSize);
    ctx.lineTo(cx + diamondSize, cy);
    ctx.lineTo(cx, cy + diamondSize);
    ctx.lineTo(cx - diamondSize, cy);
    ctx.closePath();
    ctx.stroke();
    ctx.restore();
  }

  // Apply ink + gold-halo background.
  function paintBackground(ctx, W, H, haloRadius) {
    ctx.fillStyle = '#0a0a0c';
    ctx.fillRect(0, 0, W, H);
    const g = ctx.createRadialGradient(W / 2, 0, 60, W / 2, 0, haloRadius);
    g.addColorStop(0, 'rgba(184,153,104,0.10)');
    g.addColorStop(0.55, 'rgba(184,153,104,0.025)');
    g.addColorStop(1, 'rgba(184,153,104,0)');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W, H);
  }

  // ============================================================
  // Card image — 1080 × 1350 (Instagram portrait)
  // ============================================================
  async function renderCardCanvas(opts) {
    const W = 1080, H = 1350;
    const isThai = opts.lang === 'th';
    await fontsReady();

    const canvas = document.createElement('canvas');
    canvas.width = W;
    canvas.height = H;
    const ctx = canvas.getContext('2d');
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';
    ctx.textBaseline = 'alphabetic';
    ctx.textAlign = 'center';

    paintBackground(ctx, W, H, 950);

    // Eyebrow
    ctx.fillStyle = '#b89968';
    ctx.font = '500 22px "Inter", "IBM Plex Sans Thai", sans-serif';
    drawTracked(ctx, (opts.eyebrow || '').toUpperCase(), W / 2, 200, 22, 7);

    // Card name (display serif)
    ctx.fillStyle = '#ebe4d4';
    ctx.font = isThai
      ? '300 86px "IBM Plex Sans Thai", "Cormorant Garamond", serif'
      : '300 116px "Cormorant Garamond", "IBM Plex Sans Thai", serif';
    // Fit if name is too wide
    let nameSize = isThai ? 86 : 116;
    while (ctx.measureText(opts.name).width > W - 160 && nameSize > 48) {
      nameSize -= 6;
      ctx.font = isThai
        ? `300 ${nameSize}px "IBM Plex Sans Thai", serif`
        : `300 ${nameSize}px "Cormorant Garamond", serif`;
    }
    ctx.fillText(opts.name, W / 2, 360);

    // Orientation (italic gold)
    if (opts.orientation) {
      ctx.fillStyle = '#b89968';
      ctx.font = isThai
        ? 'italic 400 30px "IBM Plex Sans Thai", serif'
        : 'italic 400 34px "Cormorant Garamond", serif';
      ctx.fillText('· ' + opts.orientation + ' ·', W / 2, 440);
    }

    // Divider
    drawDivider(ctx, W / 2, 560, 200, 8);

    // Reflective excerpt (the body)
    ctx.fillStyle = '#b9b3a4';
    ctx.font = isThai
      ? '300 32px "IBM Plex Sans Thai", serif'
      : 'italic 300 38px "Cormorant Garamond", serif';
    const lh = isThai ? 50 : 56;
    drawWrapped(ctx, opts.excerpt || '', W / 2, 670, W - 220, lh, 8);

    // Footer brand
    ctx.fillStyle = '#ebe4d4';
    ctx.font = '400 32px "Cormorant Garamond", "IBM Plex Sans Thai", serif';
    drawTracked(ctx, 'VEILA', W / 2, H - 150, 32, 20);

    // Dot ornament under wordmark
    ctx.fillStyle = '#b89968';
    ctx.beginPath();
    ctx.arc(W / 2, H - 124, 3, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#6c6a63';
    ctx.font = '400 18px "Inter", "IBM Plex Sans Thai", sans-serif';
    drawTracked(ctx, 'VEILATAROT.COM', W / 2, H - 80, 18, 5);

    return canvas;
  }

  // ============================================================
  // Reading image — 1080 × 1920 (Instagram Story)
  // ============================================================
  async function renderReadingCanvas(opts) {
    const W = 1080, H = 1920;
    const isThai = opts.lang === 'th';
    await fontsReady();

    const canvas = document.createElement('canvas');
    canvas.width = W;
    canvas.height = H;
    const ctx = canvas.getContext('2d');
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';
    ctx.textBaseline = 'alphabetic';
    ctx.textAlign = 'center';

    paintBackground(ctx, W, H, 1100);

    // Eyebrow
    ctx.fillStyle = '#b89968';
    ctx.font = '500 22px "Inter", "IBM Plex Sans Thai", sans-serif';
    drawTracked(ctx, (opts.eyebrow || '').toUpperCase(), W / 2, 200, 22, 7);

    // Title
    ctx.fillStyle = '#ebe4d4';
    ctx.font = isThai
      ? '300 76px "IBM Plex Sans Thai", serif'
      : '300 92px "Cormorant Garamond", serif';
    ctx.fillText(opts.title, W / 2, 320);

    // Subtitle
    ctx.fillStyle = '#b9b3a4';
    ctx.font = isThai
      ? 'italic 300 32px "IBM Plex Sans Thai", serif'
      : 'italic 300 38px "Cormorant Garamond", serif';
    ctx.fillText(opts.subtitle || '', W / 2, 388);

    // Divider
    drawDivider(ctx, W / 2, 470, 220, 9);

    // Five key positions. Layout math: startY + 5*blockH must finish above
    // the footer (which begins ~H-230). 560 + 5*232 = 1720, plus ~164 of
    // snippet text below the last card name → ends near 1718 with room.
    const startY = 560;
    const blockH = 232;
    const leftX = 96;
    const numWidth = 96;

    opts.positions.forEach((pos, i) => {
      const y = startY + i * blockH;

      // Position numeral (italic gold serif)
      ctx.fillStyle = '#b89968';
      ctx.font = 'italic 400 40px "Cormorant Garamond", "IBM Plex Sans Thai", serif';
      ctx.textAlign = 'center';
      ctx.fillText(pos.roman + '.', leftX + numWidth / 2, y);

      // Position label (above card name). Thai script gains visible gaps
      // when letter-spacing is applied, so for Thai we draw without
      // tracking and without uppercasing.
      ctx.fillStyle = '#b89968';
      ctx.font = isThai
        ? '500 20px "IBM Plex Sans Thai", sans-serif'
        : '600 18px "Inter", sans-serif';
      const labelX = leftX + numWidth + 10;
      if (isThai) {
        ctx.textAlign = 'left';
        ctx.fillText(pos.label || '', labelX, y - 42);
      } else {
        const labelText = (pos.label || '').toUpperCase();
        const labelWidth = ctx.measureText(labelText).width
                         + Math.max(0, labelText.length - 1) * 4;
        ctx.textAlign = 'center';
        drawTracked(
          ctx, labelText,
          labelX + labelWidth / 2, y - 42, 18, 4
        );
      }

      // Card name (ivory serif)
      ctx.fillStyle = '#ebe4d4';
      ctx.textAlign = 'left';
      ctx.font = isThai
        ? '500 40px "IBM Plex Sans Thai", serif'
        : '500 44px "Cormorant Garamond", serif';
      const cardLine = pos.cardName + (pos.reversed
        ? (isThai ? ' · กลับหัว' : ' · Reversed')
        : '');
      ctx.fillText(cardLine, leftX + numWidth + 10, y);

      // Snippet (up to 3 lines, lifted ivory for readability on mobile)
      ctx.fillStyle = '#d3ccba';
      ctx.font = isThai
        ? '400 28px "IBM Plex Sans Thai", serif'
        : '400 30px "Cormorant Garamond", serif';
      const snipX = leftX + numWidth + 10;
      const snipMaxW = W - snipX - 80;
      drawWrappedLeft(ctx, pos.snippet || '', snipX, y + 50, snipMaxW, 38, 3);
    });

    // Footer fineprint
    ctx.fillStyle = '#b9b3a4';
    ctx.font = isThai
      ? 'italic 300 30px "IBM Plex Sans Thai", serif'
      : 'italic 300 32px "Cormorant Garamond", serif';
    ctx.textAlign = 'center';
    ctx.fillText(opts.fineprint || '', W / 2, H - 230);

    // Brand wordmark
    ctx.fillStyle = '#ebe4d4';
    ctx.font = '400 32px "Cormorant Garamond", "IBM Plex Sans Thai", serif';
    drawTracked(ctx, 'VEILA', W / 2, H - 150, 32, 20);

    ctx.fillStyle = '#b89968';
    ctx.beginPath();
    ctx.arc(W / 2, H - 124, 3, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#6c6a63';
    ctx.font = '400 18px "Inter", "IBM Plex Sans Thai", sans-serif';
    drawTracked(ctx, 'VEILATAROT.COM', W / 2, H - 80, 18, 5);

    return canvas;
  }

  // Left-aligned wrap helper for the reading snippets.
  function drawWrappedLeft(ctx, text, x, y, maxWidth, lineHeight, maxLines) {
    ctx.textAlign = 'left';
    let lines = wrap(ctx, text, maxWidth);
    let truncated = false;
    if (lines.length > maxLines) {
      lines = lines.slice(0, maxLines);
      truncated = true;
    }
    lines.forEach((line, i) => {
      let toDraw = line;
      if (truncated && i === lines.length - 1) {
        toDraw = (line.replace(/[.,;:]$/, '')) + '…';
        while (ctx.measureText(toDraw).width > maxWidth && toDraw.length > 4) {
          toDraw = toDraw.slice(0, -2) + '…';
        }
      }
      ctx.fillText(toDraw, x, y + i * lineHeight);
    });
  }

  // ============================================================
  // Share sheet (slide-up)
  // ============================================================
  function openSheet(opts) {
    const sheet = document.createElement('div');
    sheet.className = 'veila-share-sheet';
    sheet.setAttribute('role', 'dialog');
    sheet.setAttribute('aria-modal', 'true');

    sheet.innerHTML = `
      <div class="vss-backdrop" data-action="close"></div>
      <div class="vss-body" role="document">
        <button class="vss-close" type="button"
                aria-label="${opts.closeLabel || 'Close'}"
                data-action="close">×</button>
        <div class="vss-eyebrow">${opts.sheetEyebrow || ''}</div>
        <div class="vss-preview"><div class="vss-loading">${opts.renderingLabel || 'Rendering…'}</div></div>
        <div class="vss-press-hint" hidden></div>
        <div class="vss-actions"></div>
      </div>
    `;
    document.body.appendChild(sheet);
    requestAnimationFrame(() => sheet.classList.add('vss-open'));

    let blob = null;
    let objectUrl = null;
    let file = null;

    function close() {
      sheet.classList.add('vss-closing');
      setTimeout(() => {
        if (objectUrl) URL.revokeObjectURL(objectUrl);
        sheet.remove();
      }, 280);
    }

    function renderActions() {
      const actions = sheet.querySelector('.vss-actions');
      actions.innerHTML = '';
      const canShareFiles = !!(navigator.canShare
        && navigator.canShare({ files: [file] }));
      // iOS Safari ignores the anchor[download] attribute for blob URLs and
      // opens a new tab instead of saving. We hide the Download button there
      // entirely and rely on native Share + the long-press hint above the
      // preview image. Desktop and Android keep the Download button.
      const showDownload = !isIOS();

      // Native Share first (most common mobile path) — promoted as primary
      if (canShareFiles) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'vss-action vss-action-primary';
        btn.dataset.action = 'native-share';
        btn.textContent = opts.shareLabel || 'Share';
        actions.appendChild(btn);
      }
      if (showDownload) {
        const dl = document.createElement('button');
        dl.type = 'button';
        dl.className = canShareFiles ? 'vss-action' : 'vss-action vss-action-primary';
        dl.dataset.action = 'download';
        dl.textContent = opts.downloadLabel || 'Download';
        actions.appendChild(dl);
      }

      const cp = document.createElement('button');
      cp.type = 'button';
      cp.className = 'vss-action';
      cp.dataset.action = 'copy-link';
      cp.textContent = opts.copyLinkLabel || 'Copy link';
      actions.appendChild(cp);
    }

    sheet.addEventListener('click', async (e) => {
      const t = e.target;
      const action = t && t.dataset && t.dataset.action;
      if (!action) return;
      switch (action) {
        case 'close':
          close();
          break;
        case 'download': {
          if (!objectUrl) return;
          // Most desktop + Android browsers honour the download attribute
          // and write a file. iOS Safari ignores it on cross-origin/blob
          // URLs and opens the blob in a new tab — in that case the
          // press-hint above the actions is already showing, telling
          // the user to long-press the preview to save to Photos.
          const a = document.createElement('a');
          a.href = objectUrl;
          a.download = opts.filename || 'veila.png';
          a.rel = 'noopener';
          a.target = '_blank';
          document.body.appendChild(a);
          a.click();
          a.remove();
          track(opts.events.exported, opts.eventParams);
          break;
        }
        case 'native-share': {
          if (!file) return;
          try {
            await navigator.share({
              files: [file],
              title: opts.shareTitle || '',
              text: opts.shareText || ''
            });
            track(opts.events.native, opts.eventParams);
          } catch (err) {
            if (err && err.name !== 'AbortError') console.error(err);
          }
          break;
        }
        case 'copy-link': {
          try {
            await navigator.clipboard.writeText(opts.pageUrl || location.href);
            const orig = t.textContent;
            t.textContent = opts.copiedLabel || 'Copied';
            t.disabled = true;
            track(opts.events.linkCopied, opts.eventParams);
            setTimeout(() => {
              t.textContent = orig;
              t.disabled = false;
            }, 1600);
          } catch (err) {
            console.error('copy failed', err);
          }
          break;
        }
      }
    });

    function isIOS() {
      const ua = navigator.userAgent || '';
      // iPad on iOS 13+ reports as Mac — check touch points to disambiguate.
      return /iPad|iPhone|iPod/.test(ua)
        || (ua.indexOf('Mac') !== -1 && (navigator.maxTouchPoints || 0) > 1);
    }

    return {
      close,
      async setBlob(b) {
        blob = b;
        objectUrl = URL.createObjectURL(b);
        file = new File([b], opts.filename || 'veila.png', { type: 'image/png' });
        const preview = sheet.querySelector('.vss-preview');
        preview.innerHTML = `<img src="${objectUrl}" alt="" />`;
        // On iOS, anchor[download] is unreliable for blobs — surface the
        // long-press hint so users have a guaranteed save path.
        if (isIOS() && opts.pressHint) {
          const hint = sheet.querySelector('.vss-press-hint');
          if (hint) {
            hint.textContent = opts.pressHint;
            hint.hidden = false;
          }
        }
        renderActions();
      }
    };
  }

  // ============================================================
  // High-level shareCard / shareReading
  // ============================================================
  async function canvasToBlob(canvas) {
    return new Promise(resolve => canvas.toBlob(resolve, 'image/png', 1.0));
  }

  async function shareCard(opts) {
    const sheet = openSheet(opts);
    try {
      const canvas = await renderCardCanvas(opts);
      const blob = await canvasToBlob(canvas);
      sheet.setBlob(blob);
    } catch (err) {
      console.error('share card render failed', err);
      sheet.close();
    }
    return sheet;
  }

  async function shareReading(opts) {
    const sheet = openSheet(opts);
    try {
      const canvas = await renderReadingCanvas(opts);
      const blob = await canvasToBlob(canvas);
      sheet.setBlob(blob);
    } catch (err) {
      console.error('share reading render failed', err);
      sheet.close();
    }
    return sheet;
  }

  window.veilaShare = { shareCard, shareReading };
})();
