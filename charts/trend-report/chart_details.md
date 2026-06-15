---
title: WebKit QA Trend Charts (last 12 months)
header-includes:
  - |
    <style>
    /* Heading anchors */
    h1[id], h2[id], h3[id], h4[id], h5[id], h6[id] {
      position: relative;
    }
    h1[id]::before, h2[id]::before, h3[id]::before, h4[id]::before, h5[id]::before, h6[id]::before {
      content: "§";
      position: absolute;
      left: -1.5em;
      opacity: 0;
      transition: opacity 0.2s ease-in-out;
    }
    h1[id]:hover::before, h2[id]:hover::before, h3[id]:hover::before, h4[id]:hover::before, h5[id]:hover::before, h6[id]:hover::before {
      opacity: 1;
    }

    /* Responsive layout improvements */
    @media (min-width: 1200px) {
      body {
        max-width: none !important;
        margin-left: 0 !important;
        margin-right: 380px; /* Space for TOC */
        padding-left: 50px;
        padding-right: 50px;
      }

      /* Preserve native image resolution for charts */
      img {
        max-width: min(1080px, calc(100vw - 450px)) !important;
      }
    }

    /* TOC improvements */
    #TOC {
      position: fixed;
      top: 20px;
      right: 20px;
      width: 340px;
      border: 1px solid #ddd;
      border-radius: 8px;
      padding: 20px;
      background-color: #f8f9fa;
      box-shadow: 0 2px 10px rgba(0,0,0,0.1);
      overflow-y: auto;
      max-height: calc(100vh - 40px);
      font-size: 0.9em;
      z-index: 1000;
    }

    #TOC ul {
      margin: 0;
      padding-left: 1em;
    }

    #TOC > ul {
      padding-left: 0;
    }

    #TOC li {
      margin: 0.25em 0;
    }

    #TOC a {
      color: #555;
      text-decoration: none;
      display: block;
      padding: 0.4em 0.6em;
      border-radius: 4px;
      transition: all 0.2s ease;
      font-size: 0.95em;
    }

    #TOC a:hover {
      color: #1a1a1a;
      background-color: #e9ecef;
      transform: translateX(4px);
    }

    /* Mobile/tablet responsive */
    @media (max-width: 1199px) {
      body {
        margin-left: 0 !important;
        margin-right: 0 !important;
        max-width: 50em !important;
        margin: 0 auto !important;
        padding: 20px !important;
      }

      #TOC {
        position: relative !important;
        top: auto !important;
        right: auto !important;
        width: auto !important;
        margin: 0 0 2rem 0 !important;
        max-height: none !important;
      }

      img {
        max-width: 100% !important;
      }
    }

    @media (max-width: 600px) {
      body {
        padding: 12px !important;
      }

      #TOC {
        padding: 15px !important;
        font-size: 0.85em !important;
      }
    }

    /* Print styles */
    @media print {
      body {
        margin-left: 0 !important;
        margin-right: 0 !important;
        max-width: none !important;
      }

      #TOC {
        display: none !important;
      }

      img {
        max-width: 100% !important;
      }
    }
    </style>
---

Trend charts for the WPE and GTK layout-test bots over the **trailing 12 months**.
**Grab any chart for your slides — click an image to open the full-size original.**

Each chart overlays all bots on one axis (a 7-day rolling mean of complete runs):

- **WPE** is red, **GTK** is green, **WPE-ARM64** is purple.
- **Release** is a solid line, **Debug** is dashed in the same port color.
- On the crashes+timeouts chart, the red dotted line marks the **50** early-exit
  threshold the CI uses to abort a run.

---

## Passing tests

[![Passing tests](./passing-last-12m-rolling7d.png)](./passing-last-12m-rolling7d.png)

## Skipped tests

[![Skipped tests](./skipped-last-12m-rolling7d.png)](./skipped-last-12m-rolling7d.png)

## Known failures (fixable)

[![Known failures](./fixable-last-12m-rolling7d.png)](./fixable-last-12m-rolling7d.png)

## Unexpected crashes + timeouts

[![Unexpected crashes and timeouts](./errors-last-12m-rolling7d.png)](./errors-last-12m-rolling7d.png)

## Unexpected failures

Text + image diffs.

[![Unexpected failures](./failures-last-12m-rolling7d.png)](./failures-last-12m-rolling7d.png)

## Regressions and flakies

Release bots only.

[![Regressions and flakies](./regr-flaky-last-12m-rolling7d.png)](./regr-flaky-last-12m-rolling7d.png)

## Regressions and flakies (% of run)

Release bots only.

[![Regressions and flakies as percent of run](./regr-flaky-pct-last-12m-rolling7d.png)](./regr-flaky-pct-last-12m-rolling7d.png)

## Ratio of interrupted runs

[![Ratio of interrupted runs](./interrupted-ratio-last-12m-rolling7d.png)](./interrupted-ratio-last-12m-rolling7d.png)

## Breakdowns

The individual kinds behind the crashes+timeouts and failures charts above.

### Crashes

[![Unexpected crashes](./crash-last-12m-rolling7d.png)](./crash-last-12m-rolling7d.png)

### Timeouts

[![Unexpected timeouts](./timeout-last-12m-rolling7d.png)](./timeout-last-12m-rolling7d.png)

### Text failures

[![Unexpected text failures](./text-last-12m-rolling7d.png)](./text-last-12m-rolling7d.png)

### Image failures

[![Unexpected image failures](./image-last-12m-rolling7d.png)](./image-last-12m-rolling7d.png)
