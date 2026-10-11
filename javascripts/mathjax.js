/* MathJax 3 配置（保持最小可用集）。
   注意：不要加 options.ignoreHtmlClass/processHtmlClass 与 document$.subscribe——
   实测二者会让 arithmatex 公式渲染成空容器（tex-mml-chtml 尤甚，tex-chtml 亦然）。
   本站未开 instant navigation，MathJax startup 的整文档自动排版即可覆盖。 */
window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"]],
    displayMath: [["\\[", "\\]"]],
    processEscapes: true,
    processEnvironments: true
  }
};
