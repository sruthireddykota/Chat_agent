// Build a nested tree from a flat { "a/b/c.py": {...} } map.

export function buildTree(files) {
  const root = { name: "", path: "", type: "folder", children: {} };
  for (const path of Object.keys(files)) {
    const parts = path.split("/");
    let node = root;
    parts.forEach((part, i) => {
      const isFile = i === parts.length - 1;
      if (isFile) {
        node.children[part] = {
          name: part,
          path,
          type: "file",
          meta: files[path],
        };
      } else {
        if (!node.children[part]) {
          node.children[part] = {
            name: part,
            path: parts.slice(0, i + 1).join("/"),
            type: "folder",
            children: {},
          };
        }
        node = node.children[part];
      }
    });
  }
  return sortNode(root);
}

// Folders first, then files; each alphabetical.
function sortNode(node) {
  if (node.type !== "folder") return node;
  const entries = Object.values(node.children).map(sortNode);
  entries.sort((a, b) => {
    if (a.type !== b.type) return a.type === "folder" ? -1 : 1;
    return a.name.localeCompare(b.name);
  });
  node.orderedChildren = entries;
  return node;
}

// All folder paths (used to expand-all by default).
export function allFolderPaths(files) {
  const set = new Set();
  for (const path of Object.keys(files)) {
    const parts = path.split("/");
    for (let i = 1; i < parts.length; i++) {
      set.add(parts.slice(0, i).join("/"));
    }
  }
  return [...set];
}

export const EXT_LANG = {
  py: "python",
  js: "javascript",
  jsx: "jsx",
  ts: "javascript",
  tsx: "jsx",
  json: "json",
  md: "markdown",
  txt: "text",
  env: "text",
  example: "text",
  yml: "text",
  yaml: "text",
  toml: "text",
  cfg: "text",
  dockerfile: "text",
};

export function langFor(name, fallback) {
  if (fallback) return fallback;
  const lower = name.toLowerCase();
  if (lower === "dockerfile") return "text";
  const ext = lower.includes(".") ? lower.split(".").pop() : lower;
  return EXT_LANG[ext] || "text";
}
