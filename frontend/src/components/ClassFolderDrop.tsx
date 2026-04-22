"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import { FolderOpen, FilePlus, X } from "lucide-react";

const SUPPORTED_EXTENSIONS = [".pdf", ".md", ".markdown", ".txt"] as const;
const MAX_FILE_BYTES = 20 * 1024 * 1024;
const MAX_TOTAL_BYTES = 50 * 1024 * 1024;

export interface SelectedFile {
  file: File;
  relativePath: string;
  sizeMB: number;
}

interface Props {
  onFilesChanged: (files: File[]) => void;
  disabled?: boolean;
}

function extOf(name: string): string {
  const dot = name.lastIndexOf(".");
  return dot === -1 ? "" : name.slice(dot).toLowerCase();
}

function isSupported(name: string): boolean {
  return (SUPPORTED_EXTENSIONS as readonly string[]).includes(extOf(name));
}

type FileEntry = { isFile: true; file(cb: (f: File) => void): void; fullPath: string };
type DirEntry = {
  isDirectory: true;
  createReader(): { readEntries(cb: (entries: AnyEntry[]) => void): void };
  fullPath: string;
};
type AnyEntry = FileEntry | DirEntry;

async function walkEntry(entry: AnyEntry, out: File[]): Promise<void> {
  if ((entry as FileEntry).isFile) {
    return new Promise((resolve) => {
      (entry as FileEntry).file((f: File) => {
        if (isSupported(f.name)) {
          // Attach the full path the browser gave us so the server side sees it.
          try {
            Object.defineProperty(f, "webkitRelativePath", {
              value: (entry as FileEntry).fullPath.replace(/^\//, ""),
            });
          } catch {
            /* some browsers disallow redefining; fine */
          }
          out.push(f);
        }
        resolve();
      });
    });
  }
  if ((entry as DirEntry).isDirectory) {
    const reader = (entry as DirEntry).createReader();
    return new Promise((resolve) => {
      const batch: AnyEntry[] = [];
      const readAll = () => {
        reader.readEntries(async (entries) => {
          if (!entries.length) {
            for (const child of batch) {
              await walkEntry(child, out);
            }
            resolve();
            return;
          }
          batch.push(...entries);
          readAll();
        });
      };
      readAll();
    });
  }
}

export default function ClassFolderDrop({ onFilesChanged, disabled }: Props) {
  const [dragOver, setDragOver] = useState(false);
  const [selected, setSelected] = useState<SelectedFile[]>([]);
  const [warning, setWarning] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const totalBytes = useMemo(
    () => selected.reduce((s, f) => s + f.file.size, 0),
    [selected]
  );

  const applySelection = useCallback(
    (raw: File[]) => {
      const accepted: SelectedFile[] = [];
      const skipped: string[] = [];
      let running = 0;
      for (const f of raw) {
        if (!isSupported(f.name)) {
          skipped.push(`${f.name} (unsupported)`);
          continue;
        }
        if (f.size > MAX_FILE_BYTES) {
          skipped.push(`${f.name} (>20 MB)`);
          continue;
        }
        if (running + f.size > MAX_TOTAL_BYTES) {
          skipped.push(`${f.name} (upload cap 50 MB reached)`);
          continue;
        }
        running += f.size;
        const rel =
          (f as File & { webkitRelativePath?: string }).webkitRelativePath ||
          f.name;
        accepted.push({
          file: f,
          relativePath: rel,
          sizeMB: f.size / (1024 * 1024),
        });
      }
      setSelected(accepted);
      setWarning(skipped.length ? skipped.join(" · ") : null);
      onFilesChanged(accepted.map((a) => a.file));
    },
    [onFilesChanged]
  );

  const handlePick = (evt: React.ChangeEvent<HTMLInputElement>) => {
    const files = evt.target.files ? Array.from(evt.target.files) : [];
    applySelection(files);
  };

  const handleDrop = async (evt: React.DragEvent<HTMLDivElement>) => {
    evt.preventDefault();
    setDragOver(false);
    if (disabled) return;

    const files: File[] = [];
    const items = evt.dataTransfer.items;
    if (items && items.length) {
      const walks: Promise<void>[] = [];
      for (const item of Array.from(items)) {
        const entry = (item as DataTransferItem & {
          webkitGetAsEntry?: () => AnyEntry | null;
        }).webkitGetAsEntry?.();
        if (entry) {
          walks.push(walkEntry(entry as unknown as AnyEntry, files));
        } else {
          const file = item.getAsFile();
          if (file) files.push(file);
        }
      }
      await Promise.all(walks);
    } else if (evt.dataTransfer.files) {
      for (const f of Array.from(evt.dataTransfer.files)) files.push(f);
    }
    applySelection(files);
  };

  const clear = () => {
    setSelected([]);
    setWarning(null);
    onFilesChanged([]);
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className="rounded-2xl p-8 text-center cursor-pointer transition-all"
        style={{
          border: `2px dashed ${
            dragOver ? "var(--duo-purple)" : "var(--duo-polar)"
          }`,
          background: dragOver ? "var(--duo-purple-light)" : "white",
          opacity: disabled ? 0.6 : 1,
        }}
        onClick={() => !disabled && inputRef.current?.click()}
      >
        <div
          className="inline-flex items-center justify-center w-14 h-14 rounded-2xl mb-3"
          style={{ background: "var(--duo-purple-light)" }}
        >
          <FolderOpen className="w-7 h-7" style={{ color: "var(--duo-purple-push)" }} />
        </div>
        <div className="text-base font-extrabold mb-1" style={{ color: "var(--duo-eel)" }}>
          Drop a class folder here
        </div>
        <div className="text-sm font-medium" style={{ color: "var(--duo-wolf)" }}>
          or click to pick — PDFs, markdown, and text files up to 20 MB each.
        </div>
        <input
          ref={inputRef}
          type="file"
          multiple
          // `webkitdirectory` / `directory` are non-standard but supported on
          // Chromium, Safari, Firefox desktop. iOS Safari falls back to
          // multi-file picker, which also works here.
          {...({ webkitdirectory: "", directory: "" } as Record<string, string>)}
          accept={SUPPORTED_EXTENSIONS.join(",")}
          style={{ display: "none" }}
          onChange={handlePick}
          disabled={disabled}
        />
      </div>

      {warning && (
        <div
          className="mt-3 p-3 rounded-2xl text-xs font-semibold"
          style={{
            background: "var(--duo-orange-light)",
            color: "var(--duo-orange-push)",
            border: "2px solid var(--duo-orange)",
          }}
        >
          Skipped: {warning}
        </div>
      )}

      {selected.length > 0 && (
        <div className="mt-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold uppercase" style={{ color: "var(--duo-wolf)" }}>
              {selected.length} file{selected.length !== 1 ? "s" : ""} · {(totalBytes / (1024 * 1024)).toFixed(1)} MB
            </span>
            <button
              type="button"
              onClick={clear}
              disabled={disabled}
              className="text-xs font-bold flex items-center gap-1"
              style={{ color: "var(--duo-red-push)" }}
            >
              <X className="w-3 h-3" />
              Clear
            </button>
          </div>
          <ul
            className="rounded-2xl overflow-hidden max-h-48 overflow-y-auto"
            style={{ border: "2px solid var(--duo-polar)", background: "white" }}
          >
            {selected.map((s) => (
              <li
                key={s.relativePath + s.file.size}
                className="px-3 py-2 flex items-center justify-between text-xs font-semibold border-b"
                style={{ color: "var(--duo-eel)", borderColor: "var(--duo-polar)" }}
              >
                <span className="flex items-center gap-2 truncate">
                  <FilePlus className="w-3 h-3 flex-shrink-0" style={{ color: "var(--duo-hare)" }} />
                  <span className="truncate">{s.relativePath}</span>
                </span>
                <span className="ml-3 font-medium" style={{ color: "var(--duo-hare)" }}>
                  {s.sizeMB.toFixed(2)} MB
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
