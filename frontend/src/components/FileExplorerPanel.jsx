import { useEffect, useMemo, useState } from "react";
import {
  ChevronRight,
  ChevronDown,
  Folder,
  FolderOpen,
  FileCode2,
  FileJson,
  FileText,
  FileCog,
  FileType2,
  Search,
  Download,
  X,
  ListTree,
  Boxes,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react";
import { buildTree, allFolderPaths, langFor } from "../utils/fileTree.js";
import { highlight } from "../utils/highlight.js";

function iconFor(name) {
  const lower = name.toLowerCase();
  if (lower.endsWith(".py")) return { Icon: FileCode2, color: "text-sky-400" };
  if (/\.(jsx?|tsx?)$/.test(lower))
    return { Icon: FileCode2, color: "text-yellow-400" };
  if (lower.endsWith(".json")) return { Icon: FileJson, color: "text-amber-400" };
  if (lower.endsWith(".md")) return { Icon: FileType2, color: "text-blue-300" };
  if (lower === "dockerfile" || lower.includes(".env"))
    return { Icon: FileCog, color: "text-slate-400" };
  if (/\.(txt|yml|yaml|toml|cfg|example)$/.test(lower))
    return { Icon: FileText, color: "text-slate-400" };
  return { Icon: FileText, color: "text-slate-400" };
}

function TreeNode({ node, depth, expanded, toggle, selected, onSelect }) {
  if (node.type === "file") {
    const { Icon, color } = iconFor(node.name);
    const active = selected === node.path;
    return (
      <button
        onClick={() => onSelect(node.path)}
        title={node.path}
        style={{ paddingLeft: depth * 14 + 8 }}
        className={`flex w-full items-center gap-2 rounded-md py-1.5 pr-2 text-left text-[13px] transition ${
          active
            ? "bg-brand-600 text-white"
            : "text-slate-300 hover:bg-slate-700/60"
        }`}
      >
        <Icon size={15} className={active ? "text-white" : color} />
        <span className="truncate">{node.name}</span>
      </button>
    );
  }

  const isOpen = expanded.has(node.path);
  return (
    <div>
      <button
        onClick={() => toggle(node.path)}
        style={{ paddingLeft: depth * 14 + 8 }}
        className="flex w-full items-center gap-1 rounded-md py-1.5 pr-2 text-left text-[13px] font-medium text-slate-200 transition hover:bg-slate-700/60"
      >
        {isOpen ? (
          <ChevronDown size={14} className="text-slate-500" />
        ) : (
          <ChevronRight size={14} className="text-slate-500" />
        )}
        {isOpen ? (
          <FolderOpen size={15} className="text-brand-300" />
        ) : (
          <Folder size={15} className="text-brand-300" />
        )}
        <span className="truncate">{node.name}</span>
      </button>
      {isOpen &&
        node.orderedChildren.map((child) => (
          <TreeNode
            key={child.path}
            node={child}
            depth={depth + 1}
            expanded={expanded}
            toggle={toggle}
            selected={selected}
            onSelect={onSelect}
          />
        ))}
    </div>
  );
}

export default function FileExplorerPanel({ files, className = "" }) {
  const paths = Object.keys(files);
  const isEmpty = paths.length === 0;
  const [search, setSearch] = useState("");
  const [expanded, setExpanded] = useState(() => new Set(allFolderPaths(files)));
  const [tabs, setTabs] = useState([]);
  const [active, setActive] = useState(null);
  const [treeOpen, setTreeOpen] = useState(true);

  useEffect(() => {
    setTabs([]);
    setActive(null);
    setSearch("");
    setExpanded(new Set(allFolderPaths(files)));
  }, [files]);

  const filteredFiles = useMemo(() => {
    if (!search.trim()) return files;
    const q = search.toLowerCase();
    const out = {};
    for (const p of paths) if (p.toLowerCase().includes(q)) out[p] = files[p];
    return out;
  }, [search, files, paths]);

  const tree = useMemo(() => buildTree(filteredFiles), [filteredFiles]);
  const searchExpanded = useMemo(
    () => (search.trim() ? new Set(allFolderPaths(filteredFiles)) : expanded),
    [search, filteredFiles, expanded]
  );

  const toggle = (path) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(path) ? next.delete(path) : next.add(path);
      return next;
    });

  const openFile = (path) => {
    setActive(path);
    setTabs((prev) => (prev.includes(path) ? prev : [...prev, path]));
  };

  const closeTab = (path, e) => {
    e.stopPropagation();
    setTabs((prev) => {
      const next = prev.filter((p) => p !== path);
      if (active === path) setActive(next[next.length - 1] ?? null);
      return next;
    });
  };

  const activeMeta = active ? files[active] : null;
  const activeLang = active
    ? langFor(active.split("/").pop(), activeMeta?.lang)
    : "text";
  const crumbs = active ? active.split("/") : [];
  const lineCount = activeMeta ? activeMeta.content.split("\n").length : 0;

  return (
    <div
      className={`flex overflow-hidden rounded-2xl border border-slate-700 bg-slate-900 ${className}`}
    >
      {/* Tree column (collapsible) */}
      {treeOpen ? (
        <div className="flex w-56 shrink-0 flex-col border-r border-slate-700 bg-slate-800/60">
          <div className="border-b border-slate-700 p-2.5">
            <div className="mb-2 flex items-center gap-1.5 px-1 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
              <ListTree size={13} /> Explorer
              <button
                onClick={() => setTreeOpen(false)}
                className="ml-auto rounded p-0.5 text-slate-400 hover:bg-slate-700 hover:text-slate-200"
                title="Collapse explorer"
              >
                <PanelLeftClose size={14} />
              </button>
            </div>
            <div className="relative">
              <Search
                size={13}
                className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500"
              />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search files…"
                className="w-full rounded-md border border-slate-700 bg-slate-900 py-1.5 pl-7 pr-2 text-xs text-slate-200 placeholder:text-slate-500 outline-none focus:border-brand-500"
              />
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-1.5">
            {tree.orderedChildren.length ? (
              tree.orderedChildren.map((child) => (
                <TreeNode
                  key={child.path}
                  node={child}
                  depth={0}
                  expanded={searchExpanded}
                  toggle={toggle}
                  selected={active}
                  onSelect={openFile}
                />
              ))
            ) : isEmpty ? (
              <p className="px-2 py-8 text-center text-xs text-slate-500">
                No files in this workspace yet.
              </p>
            ) : (
              <p className="px-2 py-6 text-center text-xs text-slate-500">
                No files match “{search}”.
              </p>
            )}
          </div>
        </div>
      ) : (
        <button
          onClick={() => setTreeOpen(true)}
          title="Show explorer"
          className="flex w-9 shrink-0 flex-col items-center gap-2 border-r border-slate-700 bg-slate-800/60 py-3 text-slate-400 hover:text-slate-200"
        >
          <PanelLeftOpen size={16} />
          <ListTree size={14} />
        </button>
      )}

      {/* Editor column */}
      <div className="flex min-w-0 flex-1 flex-col bg-slate-900">
        <div className="flex items-center gap-0.5 overflow-x-auto border-b border-slate-700 bg-slate-800/40 px-1.5 pt-1.5">
          {tabs.map((p) => {
            const name = p.split("/").pop();
            const { Icon, color } = iconFor(name);
            const on = active === p;
            return (
              <button
                key={p}
                onClick={() => setActive(p)}
                className={`group flex shrink-0 items-center gap-1.5 rounded-t-lg border-b-2 px-3 py-1.5 text-xs transition ${
                  on
                    ? "border-brand-500 bg-slate-900 text-slate-100"
                    : "border-transparent text-slate-400 hover:bg-slate-700/40"
                }`}
              >
                <Icon size={13} className={color} />
                {name}
                <span
                  onClick={(e) => closeTab(p, e)}
                  className="rounded p-0.5 text-slate-500 opacity-0 hover:bg-slate-600 hover:text-white group-hover:opacity-100"
                >
                  <X size={12} />
                </span>
              </button>
            );
          })}
        </div>

        {active && activeMeta ? (
          <>
            <div className="flex items-center gap-2 border-b border-slate-700 px-3 py-2">
              <div className="flex min-w-0 flex-1 items-center gap-1 text-xs text-slate-400">
                {crumbs.map((c, i) => (
                  <span key={i} className="flex items-center gap-1">
                    {i > 0 && (
                      <ChevronRight size={12} className="text-slate-600" />
                    )}
                    <span
                      className={
                        i === crumbs.length - 1
                          ? "font-medium text-slate-200"
                          : ""
                      }
                    >
                      {c}
                    </span>
                  </span>
                ))}
              </div>
              <span className="shrink-0 text-[11px] text-slate-500">
                {lineCount} lines ·{" "}
                {activeMeta.size?.toLocaleString?.() ?? activeMeta.content.length}{" "}
                bytes
              </span>
              <a
                href={`data:text/plain;charset=utf-8,${encodeURIComponent(
                  activeMeta.content
                )}`}
                download={active.split("/").pop()}
                className="flex shrink-0 items-center gap-1 rounded-md border border-slate-700 px-2 py-1 text-[11px] font-medium text-slate-300 hover:bg-slate-700"
              >
                <Download size={12} /> Download
              </a>
            </div>

            <div className="flex-1 overflow-auto">
              <div className="flex min-h-full text-[13px] leading-[1.6]">
                <pre className="select-none border-r border-slate-800 bg-slate-900/80 px-3 py-3 text-right text-slate-600">
                  {activeMeta.content.split("\n").map((_, i) => (
                    <div key={i}>{i + 1}</div>
                  ))}
                </pre>
                <pre className="flex-1 overflow-x-auto px-4 py-3 text-slate-100">
                  <code
                    dangerouslySetInnerHTML={{
                      __html: highlight(activeMeta.content, activeLang),
                    }}
                  />
                </pre>
              </div>
            </div>
          </>
        ) : (
          <div className="grid flex-1 place-items-center px-6 text-center">
            {isEmpty ? (
              <div>
                <Boxes size={40} className="mx-auto mb-3 text-slate-600" />
                <p className="text-sm font-medium text-slate-300">
                  This workspace is empty
                </p>
                <p className="mt-1 text-xs text-slate-500">
                  Ask the Coder agent to generate files — they&apos;ll appear
                  here for this session.
                </p>
              </div>
            ) : (
              <div className="opacity-40">
                <FileCode2 size={40} className="mx-auto mb-2 text-slate-400" />
                <p className="text-sm text-slate-400">Select a file to view it</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
