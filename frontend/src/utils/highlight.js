// Lightweight, dependency-free syntax highlighter.
// Escapes HTML first, then wraps tokens via a single left-to-right regex pass
// so matches never overlap. Returns an HTML string for dangerouslySetInnerHTML.

const COLORS = {
  comment: "#6b7280",
  string: "#9ece6a",
  number: "#ff9e64",
  keyword: "#bb9af7",
  builtin: "#7dcfff",
  tag: "#f7768e",
  attr: "#e0af68",
  heading: "#7aa2f7",
  punct: "#a9b1d6",
};

function esc(s) {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function span(type, text) {
  return `<span style="color:${COLORS[type]}">${text}</span>`;
}

const PY_KW =
  "def|class|return|import|from|as|if|elif|else|for|while|in|not|and|or|with|try|except|finally|raise|lambda|yield|pass|break|continue|global|nonlocal|assert|del|is|async|await";
const PY_BUILTIN = "None|True|False|self|cls|print|len|range|str|int|float|dict|list|set|bool";

const JS_KW =
  "const|let|var|function|return|if|else|for|while|do|import|from|export|default|class|extends|new|this|typeof|instanceof|async|await|try|catch|finally|throw|switch|case|break|continue|of|in|delete|void|yield";
const JS_BUILTIN = "null|undefined|true|false|console|window|document|Math|JSON|Object|Array|Promise|React|useState|useEffect";

function highlightGeneric(code, kw, builtin, opts = {}) {
  const parts = [];
  // Order matters: comments, strings, numbers, identifiers.
  const comment = opts.hash
    ? String.raw`#[^\n]*`
    : String.raw`\/\/[^\n]*|\/\*[\s\S]*?\*\/`;
  const strings = String.raw`"""[\s\S]*?"""|'''[\s\S]*?'''|` +
    String.raw`\`(?:\\.|[^\\\`])*\`|"(?:\\.|[^\\"])*"|'(?:\\.|[^\\'])*'`;
  const re = new RegExp(
    `(?<comment>${comment})|(?<str>${strings})|(?<num>\\b\\d+\\.?\\d*\\b)|(?<word>[A-Za-z_$][A-Za-z0-9_$]*)|(?<other>[\\s\\S])`,
    "g"
  );
  const kwSet = new Set(kw.split("|"));
  const biSet = new Set(builtin.split("|"));
  let m;
  while ((m = re.exec(code)) !== null) {
    const g = m.groups;
    if (g.comment != null) parts.push(span("comment", esc(g.comment)));
    else if (g.str != null) parts.push(span("string", esc(g.str)));
    else if (g.num != null) parts.push(span("number", g.num));
    else if (g.word != null) {
      if (kwSet.has(g.word)) parts.push(span("keyword", g.word));
      else if (biSet.has(g.word)) parts.push(span("builtin", g.word));
      else parts.push(esc(g.word));
    } else parts.push(esc(g.other));
  }
  return parts.join("");
}

function highlightJson(code) {
  const re = /("(?:\\.|[^\\"])*"\s*:)|("(?:\\.|[^\\"])*")|(\b\d+\.?\d*\b)|(\btrue\b|\bfalse\b|\bnull\b)|([\s\S])/g;
  const parts = [];
  let m;
  while ((m = re.exec(code)) !== null) {
    if (m[1] != null) parts.push(span("tag", esc(m[1])));
    else if (m[2] != null) parts.push(span("string", esc(m[2])));
    else if (m[3] != null) parts.push(span("number", m[3]));
    else if (m[4] != null) parts.push(span("keyword", m[4]));
    else parts.push(esc(m[5]));
  }
  return parts.join("");
}

function highlightMarkdown(code) {
  return code
    .split("\n")
    .map((line) => {
      if (/^#{1,6}\s/.test(line)) return span("heading", esc(line));
      let out = esc(line);
      out = out.replace(/(\*\*[^*]+\*\*)/g, (x) => span("keyword", x));
      out = out.replace(/(`[^`]+`)/g, (x) => span("string", x));
      return out;
    })
    .join("\n");
}

export function highlight(code, lang) {
  if (code == null) return "";
  switch (lang) {
    case "python":
      return highlightGeneric(code, PY_KW, PY_BUILTIN, { hash: true });
    case "javascript":
    case "jsx":
    case "js":
      return highlightGeneric(code, JS_KW, JS_BUILTIN);
    case "json":
      return highlightJson(code);
    case "markdown":
    case "md":
      return highlightMarkdown(code);
    default:
      return esc(code);
  }
}
